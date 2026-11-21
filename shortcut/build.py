#!/usr/bin/env python3
"""Builds the "Camera Roll Detox" shortcut as a plist, then signs it with macOS `shortcuts sign`.

    python3 build.py            -> dist/Camera Roll Detox.shortcut  (+ a dry-run copy that never deletes)

Action identifiers and parameter keys were read from this Mac's own Shortcuts action database
(~/Library/Shortcuts/ToolKit) and Apple's gallery shortcuts, not guessed from blog posts.
"""
import re
import os, plistlib, subprocess, sys, uuid

OBJ = "\ufffc"  # the placeholder character Shortcuts puts where a variable sits inside text
HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")

# ---------------------------------------------------------------- prompts
JUNK_PROMPT = (
    "You're cleaning someone's camera roll. Reply with exactly one word: JUNK or KEEP.\n"
    "JUNK = blurry, accidental (pocket shot, floor, ceiling, finger over lens), nearly all black or white, "
    "a one-time photo of a receipt, parking spot, menu or whiteboard, or a saved meme.\n"
    "KEEP = people, pets, places, food someone was proud of, anything that looks like a memory.\n"
    "If unsure, KEEP."
)
PARSE_PROMPT = (
    "Turn this request into JSON only, no other text:\n"
    '{"keep_screenshot_days": number or null, "min_video_minutes": number or null, "ai_check_count": number or null}\n'
    'Screenshots mentioned with no age = 30. Videos with no length = 5. Blurry, junk, random or bad photos = 150. '
    '"Everything" = 30, 5, 150. Anything not mentioned = null.\n'
    "Request: "
)
# The person picks a provider from a menu, then pastes that provider's key. (menu name, style, url, auth header,
# auth prefix, model, where to get a key). Models must see images. Claude: the studio default, low effort.
PROVIDERS = [
    ("Gemini key (free tier)", "gemini",
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
     "x-goog-api-key", "", "gemini-2.5-flash", "Get one free at aistudio.google.com/apikey"),
    ("Claude key", "anthropic", "https://api.anthropic.com/v1/messages", "x-api-key", "", "claude-opus-5-5",
     "Get one at console.anthropic.com"),
    ("OpenAI key", "openai", "https://api.openai.com/v1/chat/completions", "Authorization", "Bearer ", "gpt-4.1-mini",
     "Get one at platform.openai.com/api-keys"),
    ("OpenRouter key", "openai", "https://openrouter.ai/api/v1/chat/completions", "Authorization", "Bearer ",
     "openrouter/auto", "Get one at openrouter.ai/keys"),
    ("publik", "openai", "https://publikhq.com/api/v1/chat/completions", "Authorization", "Bearer ",
     "publik-balanced", "Paste a pk_ key from publikhq.com"),
]
# Sign in with publik, the kit's flow done from the shortcut: POST /api/v1/installs with the builds hub's public
# app token (pat_, public by design) gives this phone its own pk_ key + a claim (sign-in) link. Hub listing only,
# no new listing (studio rule). The token is read from the studio kit at build time and never printed.
PUBLIK_ORIGIN = "https://publikhq.com"
_KIT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))  # the build's copy of the studio kit
HUB_SLUG = __import__("json").load(open(os.path.join(_KIT, "hub.json")))["publikSlug"]
APP_TOKEN = open(os.path.join(_KIT, "publik-app-token.txt")).read().strip()
assert APP_TOKEN.startswith("pat_"), "kit/publik-app-token.txt must hold the hub's pat_ token"
KEY_FILE = "camera-roll-detox/ai-key.txt"  # in the Shortcuts folder, so later runs skip the setup
PROVIDER_FILE = "camera-roll-detox/ai-provider.txt"
APPLE_MODEL = "Apple Intelligence"  # the value Apple's own gallery shortcuts use (Private Cloud Compute)


def json_str(s):
    import json
    return json.dumps(s)[1:-1]  # escaped body of a JSON string, no quotes


# ---------------------------------------------------------------- plist helpers
class Flow:
    def __init__(self):
        self.actions = []

    def add(self, ident, **params):
        self.actions.append({"WFWorkflowActionIdentifier": ident, "WFWorkflowActionParameters": params})
        return params

    # actions that produce output get a UUID so later actions can point at them
    def out(self, ident, name, **params):
        u = str(uuid.uuid4()).upper()
        self.add(ident, UUID=u, **params)
        return {"Type": "ActionOutput", "OutputUUID": u, "OutputName": name}


def V(name, key=None):
    ref = {"Type": "Variable", "VariableName": name}
    if key:
        ref["Aggrandizements"] = [{"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": key}]
    return ref


REPEAT_ITEM = V("Repeat Item")
NOW = {"Type": "CurrentDate"}


def att(ref):
    return {"Value": ref, "WFSerializationType": "WFTextTokenAttachment"}


def tok(*parts):
    """Text with variables in it. parts are strings or refs."""
    s, by_range = "", {}
    for p in parts:
        if isinstance(p, str):
            s += p
        else:
            pos = len(s.encode("utf-16-le")) // 2
            by_range["{%d, 1}" % pos] = p
            s += OBJ
    return {"Value": {"string": s, "attachmentsByRange": by_range}, "WFSerializationType": "WFTextTokenString"}


def new_group():
    return str(uuid.uuid4()).upper()


F = Flow()
COND = "is.workflow.actions.conditional"
MENU = "is.workflow.actions.choosefrommenu"
# legacy If conditions
IS, CONTAINS, GREATER, HAS_VALUE = 4, 99, 2, 100


BEGINS_WITH = "begins"
TEXT_RULES = {IS: "^%s$", CONTAINS: "%s", "begins": "^%s"}


def if_(ref, cond, string=None, number=None):
    """Text checks (is / contains / begins with) go through Match Text, then If <matches> has any value.
    iOS empties the text box of a text If on import ("Please choose a value for each parameter"); a regex in
    Match Text survives, and "has any value" takes no parameter at all."""
    if cond == IS and number is not None:
        string, number = str(number), None
    if string is not None and cond in TEXT_RULES:
        pattern = TEXT_RULES[cond] % re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", string)
        ref = F.out("is.workflow.actions.text.match", "Matches", WFMatchTextPattern=pattern,
                    text=tok(ref), WFMatchTextCaseSensitive=False)
        cond, string = HAS_VALUE, None
    g = new_group()
    p = dict(GroupingIdentifier=g, WFControlFlowMode=0, WFCondition=cond,
             WFInput={"Type": "Variable", "Variable": att(ref)})
    if string is not None:
        p["WFConditionalActionString"] = string
    if number is not None:
        p["WFNumberValue"] = number
    F.add(COND, **p)
    return g


def else_(g):
    F.add(COND, GroupingIdentifier=g, WFControlFlowMode=1)


def end_if(g):
    F.add(COND, GroupingIdentifier=g, WFControlFlowMode=2, UUID=str(uuid.uuid4()).upper())


def menu(prompt, items):
    g = new_group()
    F.add(MENU, GroupingIdentifier=g, WFControlFlowMode=0,
          WFMenuPrompt=prompt, WFMenuItems=list(items))
    return g


def case(g, title):
    F.add(MENU, GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=title)


def end_menu(g):
    F.add(MENU, GroupingIdentifier=g, WFControlFlowMode=2, UUID=str(uuid.uuid4()).upper())


def set_var(name, ref):
    F.add("is.workflow.actions.setvariable", WFVariableName=name, WFInput=att(ref))


def add_to_var(name, ref):
    F.add("is.workflow.actions.appendvariable", WFVariableName=name, WFInput=att(ref))


def set_num(name, n):
    set_var(name, F.out("is.workflow.actions.number", "Number", WFNumberActionNumber=str(n)))


def set_text(name, s):
    set_var(name, F.out("is.workflow.actions.gettext", "Text", WFTextActionText=tok(s)))


def count(ref):
    return F.out("is.workflow.actions.count", "Count", Input=att(ref), WFCountType="Items")


def stop():
    F.add("is.workflow.actions.exit")


# Find Photos filter rows. Values are written both the older way (top level) and the newer way
# (inside Values / VariableOverrides) so either Shortcuts version reads them.
def f_bool(prop, value):
    return {"Property": prop, "Operator": IS, "Removable": True, "Bool": value,
            "Values": {"Bool": value, "Unit": 4}}


def f_enum(prop, value):
    sub = {"Value": value, "WFSerializationType": "WFStringSubstitutableState"}
    return {"Property": prop, "Operator": IS, "Removable": True, "Enumeration": sub,
            "Values": {"Enumeration": sub, "Unit": 4}}


def f_date_before(prop, ref):
    return {"Property": prop, "Operator": 0, "Removable": True,
            "Values": {"Unit": 4, "Date": att(ref), "VariableOverrides": {"dateValue": att(ref)}}}


def f_minutes_over(prop, ref):
    # Duration rows take a number plus a time unit; 8 = minutes in Shortcuts' unit picker
    return {"Property": prop, "Operator": GREATER, "Removable": True,
            "Values": {"Unit": 8, "Number": att(ref), "VariableOverrides": {"numberValue": att(ref)}}}


def find_photos(rows, sort=None, order=None, limit=None):
    p = {"WFContentItemFilter": {
        "Value": {"WFActionParameterFilterPrefix": 1, "WFContentPredicateBoundedDate": False,
                  "WFActionParameterFilterTemplates": rows},
        "WFSerializationType": "WFContentPredicateTableTemplate"}}
    if sort:
        p["WFContentItemSortProperty"] = sort
        p["WFContentItemSortOrder"] = order
    if limit is not None:
        p["WFContentItemLimitEnabled"] = True
        p["WFContentItemLimitNumber"] = limit if isinstance(limit, (int, float)) else att(limit)
    return F.out("is.workflow.actions.filter.photos", "Photos", **p)




def set_tok(name, t):
    set_var(name, F.out("is.workflow.actions.gettext", "Text", WFTextActionText=t))


def save_text(path, ref):
    F.add("is.workflow.actions.documentpicker.save", WFInput=att(ref), WFAskWhereToSave=False,
          WFFileDestinationPath=path, WFSaveFileOverwrite=True)


def remember(provider, key_ref):
    """AIKey + Provider for this run, and saved so later runs skip the setup."""
    set_var("AIKey", key_ref)
    p = F.out("is.workflow.actions.gettext", "Text", WFTextActionText=provider)
    set_var("Provider", p)
    save_text(KEY_FILE, key_ref)
    save_text(PROVIDER_FILE, p)


def apply_provider():
    """From Provider, set Style / URL / AuthName / AuthValue / Model. publik is the last Otherwise."""
    groups = []
    for name, style, url, auth_name, auth_pre, model, _ in PROVIDERS:
        last = name == PROVIDERS[-1][0]
        if not last:
            groups.append(if_(V("Provider"), IS, name))
        set_text("Style", style); set_text("URL", url); set_text("AuthName", auth_name)
        set_tok("AuthValue", tok(auth_pre, V("AIKey"))); set_text("Model", model)
        if not last:
            else_(groups[-1])
    for g in reversed(groups):
        end_if(g)


def ai_request(bodies):
    """bodies: {"anthropic": tok, "gemini": tok, "openai": tok}. Builds the body for Style, POSTs it to URL,
    returns the response ref."""
    ga = if_(V("Style"), IS, "anthropic")
    set_tok("Body", bodies["anthropic"])
    else_(ga)
    gg = if_(V("Style"), IS, "gemini")
    set_tok("Body", bodies["gemini"])
    else_(gg)
    set_tok("Body", bodies["openai"])
    end_if(gg)
    end_if(ga)
    headers = {"Value": {"WFDictionaryFieldValueItems": [
        {"WFItemType": 0, "WFKey": tok(V("AuthName")), "WFValue": tok(V("AuthValue"))},
        {"WFItemType": 0, "WFKey": tok("anthropic-version"), "WFValue": tok("2023-06-01")},
        {"WFItemType": 0, "WFKey": tok("anthropic-beta"), "WFValue": tok("server-side-fallback-2026-07-01")},
        {"WFItemType": 0, "WFKey": tok("Content-Type"), "WFValue": tok("application/json")},
    ]}, "WFSerializationType": "WFDictionaryFieldValue"}
    return F.out("is.workflow.actions.downloadurl", "Contents of URL",
                 WFURL=tok(V("URL")), WFHTTPMethod="POST", ShowHeaders=True,
                 WFHTTPHeaders=headers, WFHTTPBodyType="File", WFRequestVariable=att(V("Body")))


def alert(title, message):
    F.add("is.workflow.actions.alert", WFAlertActionTitle=title, WFAlertActionMessage=message,
          WFAlertActionCancelButtonShown=False)


def json_post(url, body_tok, auth=None, method="POST"):
    items = [{"WFItemType": 0, "WFKey": tok("Content-Type"), "WFValue": tok("application/json")}]
    if auth:
        items.append({"WFItemType": 0, "WFKey": tok("Authorization"), "WFValue": auth})
    p = dict(WFURL=url, WFHTTPMethod=method, ShowHeaders=True,
             WFHTTPHeaders={"Value": {"WFDictionaryFieldValueItems": items}, "WFSerializationType": "WFDictionaryFieldValue"})
    if body_tok is not None:
        body = F.out("is.workflow.actions.gettext", "Text", WFTextActionText=body_tok)
        p.update(WFHTTPBodyType="File", WFRequestVariable=att(body))
    return F.out("is.workflow.actions.downloadurl", "Contents of URL", **p)


def dict_value(ref, key):
    return F.out("is.workflow.actions.getvalueforkey", "Dictionary Value", WFInput=att(ref),
                 WFGetDictionaryValueType="Value", WFDictionaryKey=key)


def read_text(path):
    f = F.out("is.workflow.actions.documentpicker.open", "File", WFGetFilePath=path,
              WFFileErrorIfNotFound=False, WFShowFilePicker=False)
    return F.out("is.workflow.actions.detect.text", "Text", WFInput=att(f))


def load_saved_key():
    """A key set up on an earlier run: AIKey + Provider."""
    key = read_text(KEY_FILE)
    g = if_(key, HAS_VALUE)
    set_var("AIKey", key)
    set_var("Provider", read_text(PROVIDER_FILE))
    end_if(g)


def publik_sign_in():
    """Gets this phone a publik key through the hub listing, opens sign-in, checks it took. Sets AIKey or skips AI."""
    r = [F.out("is.workflow.actions.number.random", "Random Number", WFRandomNumberMinimum=lo, WFRandomNumberMaximum=hi)
         for lo, hi in ((10000000, 99999999), (1000, 9999), (100, 999), (100, 999), (100000000000, 999999999999))]
    install_id = (r[0], "-", r[1], "-4", r[2], "-8", r[3], "-", r[4])  # UUID-shaped, decimal digits are valid hex
    res = json_post(PUBLIK_ORIGIN + "/api/v1/installs", tok(
        '{"app_token":"%s","app_slug":"%s","app_version":"0.1.0","os":"iOS","device_name":"Camera Roll Detox on iPhone",'
        '"install_id":"' % (APP_TOKEN, HUB_SLUG), *install_id, '","disclosure_version":1,"dialects":["chat_completions"]}'))
    key = dict_value(res, "key")
    g = if_(key, BEGINS_WITH, "pk_")
    remember("publik", key)
    claim = dict_value(res, "claim_url")
    h = if_(claim, HAS_VALUE)
    alert("Sign in with publik", "Safari will open publik. Sign in there, then come back here and tap OK.")
    F.add("is.workflow.actions.openurl", WFInput=att(claim))
    alert("Signed in?", "Tap OK once you've signed in to publik.")
    end_if(h)
    wallet = json_post(PUBLIK_ORIGIN + "/api/v1/wallet", None, auth=tok("Bearer ", V("AIKey")), method="GET")
    w = if_(dict_value(wallet, "claim_state"), IS, "claimed")
    else_(w)
    alert("Not signed in yet", "publik doesn't show this phone as signed in, so the AI check is skipped this time. "
                               "Run it again after you sign in.")
    set_text("SkipAI", "yes")
    end_if(w)
    else_(g)
    alert("publik sign-in failed", "Couldn't reach publik. The AI check is skipped this time.")
    set_text("SkipAI", "yes")
    end_if(g)


def ai_text_reply(res):
    """Pulls the reply text out of each provider's JSON into variable Reply."""
    ga = if_(V("Style"), IS, "anthropic")
    content = F.out("is.workflow.actions.getvalueforkey", "Dictionary Value", WFInput=att(res),
                    WFGetDictionaryValueType="Value", WFDictionaryKey="content")
    last = F.out("is.workflow.actions.getitemfromlist", "Item from List", WFInput=att(content),
                 WFItemSpecifier="Last Item")  # thinking blocks come first; the text block is last
    set_var("Reply", F.out("is.workflow.actions.getvalueforkey", "Dictionary Value", WFInput=att(last),
                           WFGetDictionaryValueType="Value", WFDictionaryKey="text"))
    else_(ga)
    gg = if_(V("Style"), IS, "gemini")
    set_var("Reply", F.out("is.workflow.actions.getvalueforkey", "Dictionary Value", WFInput=att(res),
                           WFGetDictionaryValueType="Value", WFDictionaryKey="candidates.1.content.parts.1.text"))
    else_(gg)
    set_var("Reply", F.out("is.workflow.actions.getvalueforkey", "Dictionary Value", WFInput=att(res),
                           WFGetDictionaryValueType="Value", WFDictionaryKey="choices.1.message.content"))
    end_if(gg)
    end_if(ga)


def use_model(prompt_tok, result_type="Text"):
    return F.out("is.workflow.actions.askllm", "Response", WFLLMModel=APPLE_MODEL,
                 WFLLMPrompt=prompt_tok, WFGenerativeResultType=result_type)


# ================================================================= the shortcut
def build(dry_run=False):
    global F
    F = Flow()

    # --- setup: a key from an earlier run, if there is one (no question at import: iOS mangles those)
    load_saved_key()
    for n in ("ShotCount", "VidCount", "JunkCount"):
        set_num(n, 0)

    # --- Q1
    opts = ["Old screenshots", "Long videos", "Blurry and junk photos (AI)", "Everything", "I'll just tell you"]
    lst = F.out("is.workflow.actions.list", "List", WFItems=opts)
    picked = F.out("is.workflow.actions.choosefromlist", "Chosen Item", WFInput=att(lst),
                   WFChooseFromListActionPrompt="What's eating your storage? Pick as many as you want.",
                   WFChooseFromListActionSelectMultiple=True)
    set_var("Picked", picked)

    # --- how the AI runs: asked once, only when something picked needs it and there's no key yet
    for word in ("Blurry", "Everything", "tell you"):
        g = if_(V("Picked"), CONTAINS, word); set_text("NeedAI", "yes"); end_if(g)
    g = if_(V("NeedAI"), HAS_VALUE)
    k = if_(V("AIKey"), HAS_VALUE)
    else_(k)
    m = menu("Which AI should check your photos?",
             ["Apple Intelligence (iPhone 15 Pro or newer)", "Sign in with publik (free)"]
             + [p[0] for p in PROVIDERS[:-1]] + ["Skip the AI"])
    case(m, "Apple Intelligence (iPhone 15 Pro or newer)")
    case(m, "Sign in with publik (free)")
    publik_sign_in()
    for name, *_, where in PROVIDERS[:-1]:
        case(m, name)
        pasted = F.out("is.workflow.actions.ask", "Provided Input",
                       WFAskActionPrompt="Paste your %s. %s. It's saved on this iPhone only." % (name.replace(" (free tier)", ""), where))
        remember(name, pasted)
    case(m, "Skip the AI")
    set_text("SkipAI", "yes")
    end_menu(m)
    end_if(k)
    end_if(g)
    g = if_(V("AIKey"), HAS_VALUE)
    apply_provider()  # the only copy: Style / URL / auth / model for whichever key we ended up with
    end_if(g)

    g = if_(V("Picked"), CONTAINS, "Old screenshots")
    m = menu("Keep screenshots from the last...", ["Week", "Month", "3 months", "Delete all"])
    for title, n in (("Week", 7), ("Month", 30), ("3 months", 90), ("Delete all", 0)):
        case(m, title); set_num("KeepDays", n)
    end_menu(m)
    end_if(g)

    g = if_(V("Picked"), CONTAINS, "Long videos")
    m = menu("Show me videos longer than...", ["1 min", "5 min", "15 min"])
    for title, n in (("1 min", 1), ("5 min", 5), ("15 min", 15)):
        case(m, title); set_num("MinMinutes", n)
    end_menu(m)
    end_if(g)

    g = if_(V("Picked"), CONTAINS, "Blurry and junk")
    m = menu("How many recent photos should AI check?", ["50", "150", "300"])
    for n in (50, 150, 300):
        case(m, str(n)); set_num("AICount", n)
    end_menu(m)
    end_if(g)

    g = if_(V("Picked"), CONTAINS, "Everything")
    set_num("KeepDays", 30); set_num("MinMinutes", 5); set_num("AICount", 100)
    end_if(g)

    g = if_(V("Picked"), CONTAINS, "tell you")
    said = F.out("is.workflow.actions.ask", "Provided Input",
                 WFAskActionPrompt="Tell me what to clean. Like: delete screenshots older than a month and videos over 10 minutes.")
    k = if_(V("AIKey"), HAS_VALUE)
    S = json_str(PARSE_PROMPT)
    res = ai_request({
        "anthropic": tok('{"model":"claude-opus-5-5","max_tokens":2048,"output_config":{"effort":"low"},'
                         '"fallbacks":"default","messages":[{"role":"user","content":"' + S, said, '"}]}'),
        "gemini": tok('{"contents":[{"parts":[{"text":"' + S, said,
                      '"}]}],"generationConfig":{"thinkingConfig":{"thinkingBudget":0}}}'),
        "openai": tok('{"model":"', V("Model"), '","messages":[{"role":"user","content":"' + S, said, '"}]}'),
    })
    ai_text_reply(res)
    set_var("Parsed", F.out("is.workflow.actions.detect.dictionary", "Dictionary", WFInput=att(V("Reply"))))
    else_(k)
    sk = if_(V("SkipAI"), HAS_VALUE)
    alert("Needs AI", "\"I'll just tell you\" needs the AI, so it's skipped this time.")
    else_(sk)
    set_var("Parsed", use_model(tok(PARSE_PROMPT, said), "Dictionary"))
    end_if(sk)
    end_if(k)
    for key, name in (("keep_screenshot_days", "KeepDays"), ("min_video_minutes", "MinMinutes"), ("ai_check_count", "AICount")):
        val = F.out("is.workflow.actions.getvalueforkey", "Dictionary Value", WFInput=att(V("Parsed")),
                    WFGetDictionaryValueType="Value", WFDictionaryKey=key)
        h = if_(val, HAS_VALUE); set_var(name, val); end_if(h)
    end_if(g)

    m = menu("Review before deleting?", ["Yes, show me", "No, just delete"])
    case(m, "Yes, show me"); set_text("Review", "yes")
    case(m, "No, just delete"); set_text("Review", "no")
    end_menu(m)

    # --- collect: screenshots
    g = if_(V("KeepDays"), HAS_VALUE)
    cutoff = F.out("is.workflow.actions.adjustdate", "Adjusted Date", WFDate=tok(NOW), WFAdjustOperation="Subtract",
                   WFDuration={"Value": {"Magnitude": att(V("KeepDays")), "Unit": "days"},
                               "WFSerializationType": "WFQuantityFieldValue"})
    shots = find_photos([f_bool("Is a Screenshot", True), f_date_before("Date Taken", cutoff),
                         f_bool("Is Favorite", False), f_bool("Is Hidden", False)])
    add_to_var("ToDelete", shots)
    set_var("ShotCount", count(shots))
    end_if(g)

    # --- collect: long videos (always shown, deleting long videos sight unseen is scary)
    g = if_(V("MinMinutes"), HAS_VALUE)
    vids = find_photos([f_enum("Media Type", "Video"), f_minutes_over("Duration", V("MinMinutes")),
                        f_bool("Is Favorite", False)], sort="Duration", order="Longest First", limit=50)
    h = if_(vids, HAS_VALUE)
    keep = F.out("is.workflow.actions.choosefromlist", "Chosen Item", WFInput=att(vids),
                 WFChooseFromListActionPrompt="Which ones can go?", WFChooseFromListActionSelectMultiple=True)
    add_to_var("ToDelete", keep)
    set_var("VidCount", count(keep))
    end_if(h)
    end_if(g)

    # --- collect: AI junk. Use Model errors out (and stops the run) on phones without Apple
    # Intelligence, so without an AI key ask first.
    g = if_(V("SkipAI"), HAS_VALUE)
    set_var("AICount", F.out("is.workflow.actions.gettext", "Text", WFTextActionText=""))
    end_if(g)
    g = if_(V("AICount"), HAS_VALUE)
    recent = find_photos([f_enum("Media Type", "Image"), f_bool("Is a Screenshot", False), f_bool("Is Favorite", False)],
                         sort="Date Taken", order="Latest First", limit=V("AICount"))
    rg = new_group()
    F.add("is.workflow.actions.repeat.each", GroupingIdentifier=rg, WFControlFlowMode=0, WFInput=att(recent))
    small = F.out("is.workflow.actions.image.resize", "Resized Image", WFImage=att(REPEAT_ITEM),
                  WFImageResizeKey="Longest Edge", WFImageResizeLength="512")
    jpg = F.out("is.workflow.actions.image.convert", "Converted Image", WFInput=att(small),
                WFImageFormat="JPEG", WFImageCompressionQuality=0.6, WFImagePreserveMetadata=False)
    k = if_(V("AIKey"), HAS_VALUE)
    b64 = F.out("is.workflow.actions.base64encode", "Base64 Encoded", WFInput=att(jpg),
                WFEncodeMode="Encode", WFBase64LineBreakMode="None")
    P = json_str(JUNK_PROMPT)
    # The verdict check looks for JUNK anywhere in the reply JSON: same for every provider (none echo the prompt).
    set_var("Verdict", ai_request({
        "anthropic": tok('{"model":"claude-opus-5-5","max_tokens":1024,"output_config":{"effort":"low"},"fallbacks":"default",'
                         '"messages":[{"role":"user","content":[{"type":"image","source":{"type":"base64",'
                         '"media_type":"image/jpeg","data":"', b64, '"}},{"type":"text","text":"' + P + '"}]}]}'),
        "gemini": tok('{"contents":[{"parts":[{"text":"' + P + '"},{"inline_data":{"mime_type":"image/jpeg","data":"', b64,
                      '"}}]}],"generationConfig":{"maxOutputTokens":10,"thinkingConfig":{"thinkingBudget":0}}}'),
        "openai": tok('{"model":"', V("Model"), '","max_tokens":20,"messages":[{"role":"user","content":['
                      '{"type":"text","text":"' + P + '"},{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,',
                      b64, '"}}]}]}'),
    }))
    else_(k)
    set_var("Verdict", use_model(tok(JUNK_PROMPT, "\n", jpg)))
    end_if(k)
    j = if_(V("Verdict"), CONTAINS, "JUNK")
    add_to_var("Junk", REPEAT_ITEM)  # the original photo, so Delete Photos can find it
    end_if(j)
    F.add("is.workflow.actions.repeat.each", GroupingIdentifier=rg, WFControlFlowMode=2, UUID=str(uuid.uuid4()).upper())
    h = if_(V("Junk"), HAS_VALUE)
    add_to_var("ToDelete", V("Junk"))
    set_var("JunkCount", count(V("Junk")))
    end_if(h)
    end_if(g)

    # --- confirm and delete
    set_var("Total", count(V("ToDelete")))
    g = if_(V("Total"), IS, number=0)
    F.add("is.workflow.actions.alert", WFAlertActionTitle="All clean", WFAlertActionMessage="Your phone's already clean.",
          WFAlertActionCancelButtonShown=False)
    stop()
    end_if(g)

    g = if_(V("Review"), IS, "yes")
    kept = F.out("is.workflow.actions.choosefromlist", "Chosen Item", WFInput=att(V("ToDelete")),
                 WFChooseFromListActionPrompt="Untick anything you want to keep.",
                 WFChooseFromListActionSelectMultiple=True, WFChooseFromListActionSelectAll=True)
    set_var("ToDelete", kept)
    set_var("Total", count(V("ToDelete")))
    end_if(g)

    m = menu(tok("Found ", V("ShotCount"), " screenshots, ", V("VidCount"), " videos, ", V("JunkCount"),
                 " junk photos. Delete ", V("Total"), "?"), ["Delete them", "Never mind"])
    case(m, "Delete them")
    if dry_run:
        F.add("is.workflow.actions.showresult", Text=tok("DRY RUN. Would delete ", V("Total"), " items. Nothing was deleted."))
        stop()
    else:
        F.add("is.workflow.actions.deletephotos", photos=att(V("ToDelete")), entities=att(V("ToDelete")))
    case(m, "Never mind")
    stop()
    end_menu(m)

    F.add("is.workflow.actions.showresult", Text=tok(
        "Deleted ", V("Total"), " items. Cleanup would've charged you $11.99 this week. This was free.\n"
        "Changed your mind? They're in Recently Deleted for 30 days."))

    return {
        "WFWorkflowActions": F.actions,
        "WFWorkflowClientVersion": "4018.0.4",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowHasShortcutInputVariables": False,
        "WFWorkflowIcon": {"WFWorkflowIconGlyphNumber": 59511, "WFWorkflowIconStartColor": 4282601983},
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": [],
        "WFQuickActionSurfaces": [],
    }


def write(name, wf):
    os.makedirs(DIST, exist_ok=True)
    raw = os.path.join(DIST, name + ".unsigned.shortcut")
    signed = os.path.join(DIST, name + ".shortcut")
    with open(raw, "wb") as fh:
        plistlib.dump(wf, fh, fmt=plistlib.FMT_BINARY)
    if "--no-sign" in sys.argv:
        print("wrote", raw, "(unsigned, %d actions)" % len(wf["WFWorkflowActions"]))
        return
    # Signing for "anyone" (public downloads) goes through Apple's server and iCloud; with iCloud full it never
    # answers, and the hung job later DELETES its output path. So it gets its own file and only runs with --anyone.
    # Without it: "people-who-know-me", signed locally (opens for you and your contacts).
    if "--anyone" in sys.argv:
        trial = os.path.join(DIST, name + ".anyone-trial.shortcut")
        try:
            r = subprocess.run(["shortcuts", "sign", "--mode", "anyone", "--input", raw, "--output", trial],
                               capture_output=True, text=True, timeout=120)
            if r.returncode == 0 and os.path.exists(trial):
                os.replace(trial, signed)
                print("signed (anyone):", end=" ")
            else:
                sys.exit("sign --mode anyone failed for %s:\n%s%s" % (name, r.stdout, r.stderr))
        except subprocess.TimeoutExpired:
            sys.exit("sign --mode anyone hung (iCloud full?). Nothing was overwritten.")
    else:
        try:
            r = subprocess.run(["shortcuts", "sign", "--mode", "people-who-know-me", "--input", raw, "--output", signed],
                               capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired:
            sys.exit("shortcuts sign hung. Is this Mac signed in to iCloud? Unsigned plist: " + raw)
        if r.returncode != 0:
            sys.exit("sign failed for %s:\n%s%s" % (name, r.stdout, r.stderr))
        print("signed (people-who-know-me):", end=" ")
    print("built", signed, "(%d actions)" % len(wf["WFWorkflowActions"]))


if __name__ == "__main__":
    write("Camera Roll Detox", build())
    write("Camera Roll Detox (dry run)", build(dry_run=True))
