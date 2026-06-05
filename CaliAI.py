import re
import os
import json
import anthropic

# --- CONFIG ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CACHE_FILE = "cache.json"
DOCS_DIR = "docs"

_claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(RESPONSE_CACHE, f, ensure_ascii=False, indent=2)

CODES_AND_ALPHABET = '''CALIFORNIA ROLEPLAY
10-CODES AND NATO PHONETIC ALPHABET
================================================

NATO PHONETIC ALPHABET:
Used to phonetically spell out words in radio communications

A - Alpha          B - Bravo          C - Charlie        D - Delta
E - Echo           F - Foxtrot        G - Golf           H - Hotel
I - India          J - Juliet         K - Kilo           L - Lima
M - Mike           N - November       O - Oscar          P - Papa
Q - Quebec         R - Romeo          S - Sierra         T - Tango
U - Uniform        V - Victor         W - Whiskey        X - X-ray
Y - Yankee         Z - Zulu

================================================
10-CODES / GENERAL CODES
================================================

10-0 - Disappeared
10-1 - Frequency Change
10-2 - Negative
10-3 - Stop Transmitting
10-4 - Acknowledged
10-5 - Relay Message
10-6 - Busy
10-7 - Out of Service
10-8 - In Service
10-9 - Repeat
10-10 - Fight in Progress
10-11 - Traffic Stop
10-12 - Standby
10-13 - Shots Fired
10-15 - Subject in custody en route to Station
10-16 - Stolen Vehicle
10-17 - Suspicious Circumstances (Suspicious Person)
10-18 - Disturbance
10-19 - Active Ride Along
10-20 - Location
10-21 - Call/Check Discord
10-22 - Disregard
10-23 - Arrived on Scene
10-25 - Do you have Contact With ?
10-26 - ETA
10-27 - Driver's License Check for Valid
10-28 - Vehicle License Plate Check
10-29 - NCIC Warrant Check
10-30 - Wanted Person
10-31 - Dangerous/Armed Person
10-32 - Additional Unit Requested (Code 1-2-3)
10-34 - Completed Assignment - No Report
10-35 - Not Wanted/No Warrants
10-36 - Situation Under Control
10-37 - Completed last Assignment
10-38 - Suspicious Vehicle
10-39 - Police Officer
10-41 - Beginning Tour of Duty
10-42 - Ending Tour of Duty
10-43 - Information about ?
10-44 - Park, Walk, & Talk
10-45 - Street Race
10-46 - EDP (Emotionally Disturbed Person)
10-50 - Vehicle Accident
10-51 - Request Towing Service
10-52 - Request EMS
10-53 - Request Fire Department
10-54 - Hit and Run
10-55 - Intoxicated Driver
10-56 - Intoxicated Pedestrian
10-60 - Animal Attack
10-61 - Larceny
10-62 - Kidnapping
10-63 - Radio Check
10-64 - Assault
10-65 - Armed Robbery
10-66 - Reckless Driver
10-67 - Fire
10-70 - Foot Pursuit
10-71 - Request Supervisor at Scene
10-73 - Advise Status
10-76 - In Route
10-80 - Vehicle Pursuit
10-85 - Delay due to
10-86 - Any Traffic for Me?
10-88 - Request District Assistance
10-89 - Request Major Assistance
10-90 - Bank Alarm
10-91 - Unnecessary use of Radio
10-93 - Warning
10-94 - Aircraft Emergency
10-97 - Request Prisoner Transport
10-99 - Officer In Distress EXTREME EMERGENCY ONLY

11-44 - Person Deceased

CODE 5 - Felony Stop / High Risk Stop
CODE 6 - In The Area Of

SIGNAL 11 - Running Radar
SIGNAL 13 - Clear for Crime Broadcast
SIGNAL 100 - HOLD ALL BUT EMERGENCY TRAFFIC
'''

DOCUMENT_KEYWORDS = {
    "gsop": [
        "global sop", "standard operating procedures", "chain of command", "in-character", "ooc",
        "rto", "radio", "weapon", "vehicle", "uniform", "transfer", "resignation", "department",
        "jurisdiction", "headtag", "duty blip", "tac", "tactical", "general rules", "server rules",
        "basic rules", "2 life", "two life", "break character", "mag dump", "corrupt rp",
        "switch department", "off duty", "on duty", "flashbang", "scene command", "reinstate",
        "terminated", "how many command", "use of force", "pursuit", "opposing lane",
        "corrupt roleplay", "department strike", "pre main", "main leo", "main fed",
        "hour requirement", "hours requirement", "meet hours", "duty hours",
    ],
    "civilian": [
        "punishment", "ban", "jail", "rdm", "vdm", "failrp", "chat offense", "discord", "slur",
        "harassment", "spam", "terrorism", "ltap", "penalty", "grief", "kos", "kill on sight",
        "combat log", "leave during", "mod menu", "cheat", "troll", "minge", "unrealistic driving",
        "sexual rp", "nsfw", "impersonate", "death threat", "server advert", "ddos", "got banned",
        "how long ban", "got jailed", "mass rdm", "mass vdm", "no intent", "ruining", "livestream",
    ],
    "pilots": [
        "pilot", "aircraft", "flying", "helicopter", "plane", "altitude", "airspace", "runway",
        "aviation", "buzzard", "maverick", "can i fly", "no fly", "fly over", "minimum altitude",
        "land on", "fort zancudo", "zancudo", "weather", "air unit", "pilot license", "flying over",
        "fly near", "restricted", "no fly zone", "crash land", "air",
    ],
    "nsb": [
        "promotion", "activity", "patrol agent", "supervisor", "rank requirement", "evaluation ticket",
        "rank cooldown", "probationary agent", "nsb promotion", "nsb rank", "rank up", "get promoted",
        "how many hours", "hours needed", "next rank", "activity requirement", "host training",
        "host recruitment", "week in rank", "eligible for promotion", "how do i advance",
        "open evaluation", "hours for rank",
        "nsb", "national security bureau", "fto", "miranda", "medical rp", "response code",
        "plate format", "callsign", "lethal force", "pit vehicle", "federal intelligence",
        "commanding presence", "operational principles", "nsb overview", "nsb purpose",
        "nsb conduct", "nsb protocol", "nsb radio", "nsb training", "use of force", "signal 100",
        "break break break", "xxnsb", "federal fugitive", "arrest", "dead body", "check pulse",
        "dispatch", "self dispatch", "rto format", "radio format", "how to radio", "call out",
        "pit maneuver", "code 1", "code 2", "code 3", "code 4", "lethal", "taser", "baton",
        "federal offense", "less lethal", "verbal command", "officer presence",
    ],
    "codes": [
        "10-code", "10-", "signal", "nato", "phonetic", "alphabet", "frequency change", "disregard",
        "acknowledged", "officer in distress", "shots fired", "traffic stop", "all the codes",
        "list of codes", "what does 10", "what is 10", "radio code", "nato letter", "what letter",
        "what does code", "10 code", "what does signal",
    ],
    "leo": [
        "leo", "leo punishment", "leo offense", "leo member", "leo suspension", "leo demotion",
        "leo termination", "leo blacklist", "member punishment", "department suspension",
        "no badge", "badge in rto", "meta gaming", "metagaming", "low effort rp", "power gaming",
        "powergaming", "bp vehicle", "bulletproof vehicle", "no fear rp", "bog", "roe",
        "rules of engagement", "gun rules", "excessive force", "insubordination", "life rules",
        "abuse of mechanics", "exploit", "not in leo rto", "leo rto", "poaching", "nuking discord",
        "leo corruption", "leo conduct", "leo guidelines", "leo rule", "leo officer",
        "leo fail rp", "leo unprofessional", "leo outfit", "leo vehicle", "leo recruit",
    ],
    "bb": [
        "bb", "boosted boiz", "boosted boys", "boosted boiz sop", "boosted boiz rules",
        "boosted boiz guidelines", "boosted boiz car group", "boosted boiz street racing",
        "boosted boiz safety", "boosted boiz conduct", "boosted boiz gun rules",
        "boosted boiz weapons", "boosted boiz firearm", "boosted boiz pistol",
        "boosted boiz rifle", "boosted boiz shooting", "boosted boiz shoot police",
        "boosted boiz leo", "boosted boiz law enforcement", "boosted boiz evade",
        "boosted boiz illegal", "boosted boiz street race", "boosted boiz race",
        "boosted boiz vdm", "boosted boiz rdm", "boosted boiz vehicle abuse",
        "boosted boiz headtag", "boosted boiz head tag", "boosted boiz head-tag",
        "boosted boiz drugs", "boosted boiz alcohol", "boosted boiz conduct",
        "boosted boiz incident", "boosted boiz report incident", "boosted boiz accident",
        "boosted boiz termination", "boosted boiz blacklist", "boosted boiz removal",
        "boosted boiz group leader", "boosted boiz officer in charge",
        "boosted boiz reputation", "boosted boiz community",
        "boosted boiz vehicle maintenance", "boosted boiz car condition",
        "boosted boiz speed", "boosted boiz reckless",
        "boosted boiz background", "boosted boiz history", "ace manhattan",
        "bb sop", "bb rules", "bb gun rules", "bb weapons", "bb headtag",
        "bb street racing", "bb car group", "bb race", "bb evade",
        "bb conduct", "bb safety", "bb termination", "bb blacklist",
        "car club rules", "street racing sop", "street racing rules",
        "street racing gun rules", "car enthusiast group",
        "how to join boosted boiz", "join boosted boiz", "boosted boiz recruitment",
    ],
    "rhpd": [
        "rhpd", "rpd", "redwood hills police", "redwood hills police department",
        "rhpd roster", "rhpd rank", "rhpd member", "rhpd members",
        "rhpd chief", "rhpd captain", "rhpd sergeant", "rhpd officer", "rhpd cadet",
        "rhpd high command", "rhpd low command", "rhpd command",
        "rpd-01", "rpd-09", "rpd-10", "rpd-11", "rpd-12", "rpd-16",
        "rpd-26", "rpd-27", "rpd-28", "rpd-29", "rpd-35",
        "rpd-48", "rpd-49", "rpd-50", "rpd-51", "rpd-52", "rpd-54", "rpd-55",
        "rpd-57", "rpd-58", "rpd-59", "rpd-68", "rpd-70",
        "rpd-99", "rpd-101", "rpd-102", "rpd-103", "rpd-104",
        "ck-01", "ck-02", "ck-", "rhpd cadet callsign",
        "c. titan", "river j rhpd", "john c rhpd", "malcove mike", "j. rodriguez rhpd",
        "paul b rhpd", "john w rhpd", "baz b rhpd", "l. reeves", "e. mayo",
        "j. paul rhpd", "may h", "r. guzman", "c. mollek", "j. mike rhpd",
        "j. cash", "c. williams rhpd", "elite z", "j. max rhpd", "j. james rhpd",
        "thorton b", "c. chan", "j. west rhpd", "j. johnson rhpd", "jimmy j rhpd",
        "b. bergz", "a. cat", "c. shaw",
        "rhpd master sergeant", "rhpd sergeant 1st class", "rhpd corporal",
        "rhpd officer iii", "rhpd officer ii", "rhpd reserve",
        "rhpd trial high command", "rhpd trial low command",
        "rhpd major", "rhpd 1st lieutenant", "rhpd 2nd lieutenant",
        "rhpd master sergeant", "rhpd swat", "rhpd teu",
        "rhpd activity", "rhpd fta", "rhpd fto",
        "rhpd loa", "rhpd reserve status",
        "rhpd sop", "rhpd rules", "rhpd guidelines", "rhpd policies",
        "rhpd conduct", "rhpd mission statement", "rhpd core values", "rhpd integrity",
        "rhpd disciplinary", "rhpd strike", "rhpd verbal warning", "rhpd written warning",
        "rhpd retraining", "rhpd termination", "rhpd blacklist",
        "rhpd activity requirement", "rhpd 5 hours", "rhpd hours",
        "rhpd promotion policy", "rhpd double promo", "rhpd promotion cooldown",
        "rhpd rto", "rhpd radio", "rhpd radio etiquette", "rhpd 10 codes",
        "rhpd signal 100", "rhpd code 5", "rhpd felony stop",
        "rhpd uniform", "rhpd vehicle", "rhpd vehicle structure",
        "rhpd weapon", "rhpd loadout", "rhpd carbine", "rhpd shotgun",
        "rhpd ap pistol", "rhpd swat weapon", "rhpd heavy weapon",
        "rhpd chain of command", "rhpd coc", "rhpd rank duties",
        "rhpd traffic stop", "rhpd 10-11", "rhpd positioning",
        "rhpd high risk stop", "rhpd code 5 stop", "rhpd felony",
        "rhpd pursuit", "rhpd vehicle pursuit", "rhpd pit maneuver",
        "rhpd spike strips", "rhpd self attach",
        "rhpd property check", "rhpd personal check",
        "rhpd supervisor", "rhpd 10-71", "rhpd call supervisor",
        "rhpd response policy", "rhpd code 1", "rhpd code 2", "rhpd code 3",
        "rhpd scene command", "rhpd mva", "rhpd 10-50",
        "rhpd use of force", "rhpd lethal force", "rhpd discharge firearm",
        "rhpd after action", "rhpd clearance policy",
        "rhpd leave of absence", "rhpd loa policy", "rhpd loa 7 days",
        "rhpd loa 14 days", "rhpd loa cooldown", "rhpd long term loa",
        "rhpd transfer", "rhpd transfer policy", "rhpd 60 day",
        "rhpd radio frequency", "rhpd in game frequency",
        "rhpd name structure", "rhpd name format", "rhpd callsign format",
        "rhpd license plate", "rhpd plate", "rhpd plate format", "##rhp###",
        "rhpd cad", "rhpd cad system", "rhpd headtag",
        "rhpd on duty", "rhpd 10-1 channel",
        "rhpd subdivision", "rhpd swat", "rhpd speed freaks", "rhpd teu",
        "rhpd pursuit unit", "rhpd offroad", "rhpd off road",
        "rockford hills", "rockford hills police", "rockford hills pd",
        "rhpd cadet automatic strike", "rhpd officer 1 strike",
        "how to join rhpd", "join rhpd", "rhpd recruitment",
    ],
    "metro": [
        "metro", "mpd", "metro police", "metro police department",
        "metro sop", "metro rules", "metro guidelines", "metro policies",
        "metro rank", "metro promotion", "metro activity", "metro hours",
        "metro loa", "metro leave", "metro strike", "metro suspension",
        "metro termination", "metro discipline", "metro punishment", "metro conduct",
        "metro chain of command", "metro coc", "metro command structure",
        "metro chief of police", "metro deputy chief", "metro assistant chief",
        "metro chief of staff", "metro colonel", "metro lieutenant colonel",
        "metro major", "metro captain", "metro 1st lieutenant", "metro 2nd lieutenant",
        "metro master sergeant", "metro staff sergeant", "metro sergeant",
        "metro corporal", "metro lance corporal", "metro officer",
        "metro officer i", "metro officer ii", "metro officer iii",
        "metro cadet", "metro trainee",
        "metro high command", "metro low command", "metro supervisor",
        "metro trial high command", "metro trial low command",
        "metro subdivision", "metro swat", "metro tactical air",
        "metro marksman", "metro breaching", "metro negotiation",
        "metro giu", "metro gang investigation", "metro undercover",
        "metro canine", "metro k9", "metro narcotics",
        "metro teu", "metro traffic enforcement", "metro heat",
        "metro mbu", "metro motor bike", "metro offroad", "metro air",
        "metro marine", "metro bicycle", "metro search rescue",
        "metro vehicle", "metro plate", "mpd plate", "##mpd###",
        "metro uniform", "metro loadout", "metro weapon",
        "metro combat pistol", "metro carbine", "metro shotgun",
        "metro taser", "metro nightstick", "metro less lethal",
        "metro callsign", "metro 1n-", "metro identification",
        "metro cad", "metro cad policy", "metro status",
        "metro rto", "metro radio", "metro radio etiquette",
        "metro breaking character", "metro break character",
        "metro scene command", "metro priority scene", "metro non priority",
        "metro dohs", "metro homeland security",
        "metro evaluation", "metro evaluation ticket", "metro promotion ticket",
        "metro asking promotion", "metro double promotion",
        "metro rank lock", "metro time in rank",
        "metro reserves", "metro reserve status", "metro 1 hour",
        "metro resignation", "metro resign", "metro transfer",
        "metro removal from ranks", "metro high command removal",
        "metro loa 14 days", "metro loa 30 days", "metro loa extension",
        "metro discord", "metro discord rules",
        "metro code of conduct", "metro professionalism",
        "metro activity requirement", "metro weekly requirement",
        "andrew z metro", "mpd andrew z",
        "how to join metro", "join metro police", "metro recruitment",
        "metro san andreas", "metro community",
    ],
    "safr": [
        "safr", "ems", "emergency medical services", "fire department", "fire rescue",
        "safr sop", "ems sop", "ems rules", "ems guidelines", "ems policies",
        "paramedic", "paramedics", "emt", "emt-b", "firefighter", "fire fighter",
        "ems rank", "ems promotion", "ems activity", "ems hours",
        "ems loa", "ems leave", "ems strike", "ems suspension",
        "ems termination", "ems discipline", "ems punishment", "ems conduct",
        "ems chain of command", "ems coc", "ems command",
        "ems captain", "ems lieutenant", "ems chief", "ems administration",
        "ems clock in", "clock in abuse", "revive permission", "ems revive",
        "ems reinstatement", "ems reserves", "ems retirement",
        "ems loa policy", "ems 30 day loa", "ems 60 day loa",
        "ems radio", "ems rto", "ems callsign", "ems rto format", "1f-",
        "ems uniform", "ems apparatus", "ems vehicle",
        "ems driving", "code 1 ems", "code 2 ems", "code 3 ems",
        "ems speed limit", "ems 85 mph", "ems 75 mph", "ems 100 mph",
        "ems staging", "ems stations", "ems hospital",
        "ems call allocation", "ems dispatch", "ems self dispatch",
        "10-99 ems", "officer down ems", "ems down", "ems stage",
        "incident command ems", "ems scene command",
        "patient treatment", "patient priority", "treat suspect first",
        "right to refuse", "refuse treatment", "ems transport",
        "priority 1 transport", "priority 2 transport", "priority 3 transport",
        "ems transport rto", "ems transporting", "ems hospital check in",
        "transporting suspect", "suspect transport ems",
        "fire type", "chemical fire", "electrical fire", "normal fire",
        "fire hose", "attack line", "foam hose", "foam gun", "water gun",
        "fire extinguisher", "scba", "turnout gear", "fire scene",
        "fire hydrant", "supply line", "tank refill", "fire tank",
        "engine ems", "ladder ems", "brush ems", "fr-10", "lb-3387",
        "fire tank duration", "tank meter",
        "10-50 ems", "mva ems", "motor vehicle accident ems",
        "spreaders", "jaws of life", "ems spreaders", "saw command",
        "/stretcher", "/fan", "/stabiliser", "/saw", "/spreaders",
        "ems passive", "passive department", "ems no weapons", "ems pursuit",
        "ems pursuit rules", "ems failrp", "ems respawn",
        "ems trainee", "ems trainee clock in", "ems training",
        "ems medical rp", "ems check pulse", "ems priority",
        "rescue apparatus", "medevac", "firehawk", "ems coroner",
        "how to join ems", "join ems", "join safr", "ems recruitment",
    ],
    "satf": [
        "satf", "san andreas task force", "satf sop", "satf rules", "satf guidelines",
        "satf rank", "satf promotion", "satf activity", "satf hours",
        "satf loa", "satf leave", "satf strike", "satf suspension",
        "satf termination", "satf discipline", "satf punishment", "satf conduct",
        "satf director", "satf deputy director", "satf assistant director",
        "satf chief", "satf assistant chief", "satf colonel", "satf lieutenant colonel",
        "satf captain", "satf commander", "satf 1st lieutenant", "satf 2nd lieutenant",
        "satf master sergeant", "satf staff sergeant", "satf sergeant",
        "satf master corporal", "satf senior corporal", "satf corporal",
        "satf master officer", "satf senior officer", "satf officer",
        "satf officer in training", "satf oit",
        "satf high command", "satf low command", "satf supervisory command",
        "satf chain of command", "satf coc", "satf command structure",
        "satf subdivision", "satf sfo", "satf achd", "satf k9", "satf siu",
        "satf giu", "satf esu", "satf tems", "satf air division", "satf canine",
        "satf gang investigation", "satf special investigations",
        "satf special field operations", "satf emergency service",
        "satf vehicle", "satf plate", "satf plate format", "stf plate",
        "satf uniform", "satf /org",
        "satf weapon", "satf weapons", "satf carbine", "satf shotgun",
        "satf bean bag", "satf baton", "satf combat pistol",
        "satf use of force", "satf deadly force", "satf force levels",
        "satf capability opportunity intent", "satf coi",
        "satf miranda", "satf miranda rights",
        "satf traffic stop", "satf 10-11", "satf felony stop", "satf code 5",
        "satf pursuit", "satf 10-80", "satf foot pursuit", "satf 10-70",
        "satf bls", "satf basic life support", "satf ems",
        "satf cad", "satf cad policy", "satf radar", "satf plate reader",
        "satf rto", "satf radio", "satf dispatch", "satf response codes",
        "satf code 1", "satf code 2", "satf code 3", "satf code 4",
        "satf duty", "satf on duty", "satf off duty", "satf 10-41", "satf 10-42",
        "satf callsign", "satf identification", "satf headtag", "satf badge",
        "satf mission", "satf jurisdiction", "satf statewide",
        "satf p lallero", "satf j peter", "satf j rizz", "satf k johanson",
        "satf powergaming", "satf metagaming",
        "how to join satf", "join satf", "satf recruitment",
    ],
    "sbpd": [
        "sbpd", "south beach police", "south beach police department",
        "sbpd sop", "sbpd rules", "sbpd guidelines", "sbpd policies",
        "sbpd rank", "sbpd promotion", "sbpd activity", "sbpd hours",
        "sbpd loa", "sbpd leave", "sbpd strike", "sbpd suspension",
        "sbpd termination", "sbpd discipline", "sbpd punishment",
        "sbpd chain of command", "sbpd coc", "sbpd command structure",
        "sbpd chief of police", "sbpd deputy chief", "sbpd assistant chief",
        "sbpd chief of staff", "sbpd captain", "sbpd watch commander",
        "sbpd lieutenant", "sbpd staff sergeant", "sbpd senior sergeant",
        "sbpd sergeant", "sbpd corporal", "sbpd officer", "sbpd officer i",
        "sbpd officer ii", "sbpd officer iii", "sbpd probationary officer",
        "sbpd reserve officer", "sbpd cadet",
        "sbpd high command", "sbpd low command", "sbpd supervisor",
        "sbpd vehicle", "sbpd vehicles", "sbpd speed", "sbpd 180 mph",
        "sbpd 225 mph", "sbpd heat", "sbpd pursuit", "sbpd driving",
        "sbpd locked vehicle", "sbpd lightbar", "sbpd visor",
        "sbpd uniform", "sbpd uniforms", "sbpd hair", "sbpd tattoo",
        "sbpd formal uniform", "sbpd ceremonial",
        "sbpd weapon", "sbpd weapons", "sbpd mag dump", "sbpd taser",
        "sbpd tactical weapon", "sbpd swat weapon",
        "sbpd subdivision", "sbpd srt", "sbpd tac", "sbpd gang unit",
        "sbpd air unit", "sbpd k9", "sbpd traffic enforcement",
        "sbpd teu", "sbpd undercover", "sbpd uc",
        "sbpd cad", "sbpd cad policy", "sbpd 10-8", "sbpd 10-7",
        "sbpd rto", "sbpd radio", "sbpd dispatch", "sbpd 10 codes",
        "sbpd use of force", "sbpd force continuum", "sbpd lethal",
        "sbpd verbal warning", "sbpd written warning",
        "sbpd naming", "sbpd name format", "sbpd callsign",
        "sbpd headtag", "sbpd badge", "sbpd identify",
        "sbpd promotion cooldown", "sbpd 7 day", "sbpd 14 day",
        "sbpd time in rank", "sbpd performance",
        "sbpd mission", "sbpd los angeles", "sbpd jurisdiction",
        "sbpd patrol", "sbpd training", "sbpd events",
        "south beach pd", "south beach cop",
        "how to join sbpd", "join sbpd", "sbpd recruitment",
    ],
    "ncea": [
        "ncea", "national criminal enforcement agency", "ncea sop", "ncea rules",
        "ncea agent", "ncea rank", "ncea promotion", "ncea activity", "ncea hours",
        "ncea loa", "ncea leave", "ncea strike", "ncea suspension", "ncea termination",
        "ncea blacklist", "ncea discipline", "ncea punishment", "ncea conduct",
        "ncea director", "ncea deputy director", "ncea assistant director",
        "ncea chief of staff", "ncea deputy chief of staff", "ncea lt commander",
        "ncea major", "ncea captain", "ncea special agent in charge", "ncea sac",
        "ncea supervisory special agent", "ncea senior special agent",
        "ncea special agent", "ncea agent first class", "ncea probationary agent",
        "ncea high command", "ncea low command", "ncea supervisor", "ncea patrol",
        "ncea chain of command", "ncea coc", "ncea command structure",
        "ncea callsign", "ncea-01", "ncea-02", "ncea-03", "billy m ncea",
        "ncea uniform", "ncea vehicle", "ncea plate", "ncea weapon", "ncea loadout",
        "ncea taser", "ncea baton", "ncea carbine", "ncea shotgun", "ncea pistol",
        "ncea use of force", "ncea force level", "ncea roe", "ncea engagement rules",
        "ncea de-escalation", "ncea lethal force", "ncea protocol null",
        "ncea threat classification", "threat code green", "threat code amber",
        "threat code red", "threat code black", "threat code white",
        "ncea clearance", "ncea clearance level", "ncea omega clearance",
        "ncea alpha clearance", "ncea beta clearance",
        "ncea mission", "ncea jurisdiction", "ncea authority", "ncea mandate",
        "ncea deployment", "ncea containment", "ncea investigation",
        "ncea omega lockdown", "ncea clean sweep", "ncea data purge",
        "ncea emergency protocol", "ncea pre-mission", "ncea debrief",
        "ncea after action report", "ncea aar", "ncea psychological evaluation",
        "ncea training", "ncea bootcamp", "ncea certification", "ncea bls",
        "ncea heat certification", "ncea narcotics", "ncea off road",
        "ncea rto", "ncea radio", "ncea rto etiquette",
        "ncea cad", "ncea cad policy", "ncea naming policy",
        "ncea identifying", "ncea headtag", "ncea badge",
        "ncea subdivision", "ncea rip", "ncea gost", "ncea viper", "ncea cort",
        "ncea maps", "ncea k9", "ncea division alpha",
        "rapid intervention pursuit", "gang operations surveillance team",
        "violent intervention pursuit", "critical operations rescue",
        "marine air patrol section", "ncea canine",
        "ncea promotional requirements", "ncea double promo", "ncea exam",
        "ncea 5 hours", "ncea 40 hours", "ncea weekly", "ncea monthly",
        "ncea recruitment log", "ncea sergeant exam", "ncea low command exam",
        "ncea loa 14 days", "ncea return loa",
        "ncea organizational structure", "directorate alpha",
        "division i ncea", "division c ncea", "division e ncea",
    ],
    "talon_security": [
        "talon security", "talon", "talon sop", "talon rules", "talon guidelines",
        "talon security sop", "talon security rules", "talon security agent",
        "talon security rank", "talon security callsign", "ts-", "ta-", "tstalon",
        "talon founder", "talon chief of security", "talon operations director",
        "talon divisional director", "talon director of field operations",
        "talon director of tactical operations", "talon lead supervisor",
        "talon field supervisor", "talon head operative", "talon elite operative",
        "talon lead operative", "talon senior operative", "talon junior operative",
        "talon security agent", "talon trial agent",
        "talon chain of command", "talon coc", "talon high command", "talon low command",
        "talon supervisors", "talon operatives", "talon probationary",
        "talon activity", "talon hours", "talon weekly hours", "talon hour requirement",
        "talon 6 hours", "talon 3 hours", "talon restricted hours",
        "talon promotion", "talon promotion policy", "talon logs",
        "talon uniform", "talon custom uniform", "talon uniform approval",
        "talon weapon", "talon weapons", "talon authorized weapons", "talon prohibited weapons",
        "talon ar", "talon smg", "talon pistol", "talon taser", "talon baton",
        "talon bean bag", "talon no suppressors", "talon no drum mag",
        "talon vehicle", "talon vehicles", "talon escalade", "talon cts",
        "talon plate", "talon black vehicle", "talon 140 mph",
        "talon pursuit", "talon no pursuit", "talon traffic laws",
        "talon roe", "talon rules of engagement", "talon use of force",
        "talon de-escalation", "talon self defense", "talon defense of property",
        "talon force report", "talon citizens arrest", "talon ziptie",
        "talon rto", "talon radio", "talon on duty", "talon clock in",
        "talon subdivision", "talon rtd", "talon k9", "talon vanguard",
        "talon nest", "talon soar", "talon air division", "talon undercover",
        "talon canine", "talon aerial reconnaissance", "talon recruitment training",
        "talon confidential", "talon blacklist", "talon termination",
        "talon harassment", "talon bullying", "talon conduct",
        "talon clocking in", "talon security agent rank", "talon 3 jobs",
        "how to join talon", "join talon security", "talon trial",
        "security business", "security company", "private security",
    ],
    "weazel_news": [
        "weazel news", "weazel", "weazel news sop", "weazel news rules", "weazel news guidelines",
        "weazel news chain of command", "weazel news coc", "weazel news rank",
        "weazel news ceo", "weazel news coo", "weazel news cfo", "weazel news cmo",
        "weazel news chro", "weazel news chief editor", "weazel news editor",
        "weazel news branch manager", "weazel news journalist", "weazel news reporter",
        "weazel news investigative journalist", "weazel news intern",
        "weazel news promotion", "weazel news activity", "weazel news hours",
        "weazel news uniform", "weazel news vehicle", "weazel news livery",
        "weazel news discipline", "weazel news strike", "weazel news suspension",
        "weazel news termination", "weazel news warning", "weazel news verbal warning",
        "weazel news written warning", "weazel news discipline structure",
        "weazel news location", "weazel plaza", "weazel hq", "weazel branch office",
        "732 weazel", "662 weazel",
        "weazel news rp", "weazel news roleplay", "weazel news passive rp",
        "weazel news radio", "weazel news frequency", "weazel news vc",
        "weazel news voice chat", "weazel news on duty",
        "weazel news coverage", "weazel news broadcast", "weazel news report",
        "weazel news breaking news", "weazel news investigation",
        "weazel news backstory", "richie weazel brown", "weazel news history",
        "weazel news mission", "weazel news vision",
        "media", "news reporter", "news journalist", "news channel", "tv news",
        "news coverage", "news broadcast", "media outlet", "press", "journalism",
        "how to join weazel", "join weazel news", "weazel news recruitment",
        "weazel news reduced hours", "weazel news loa", "weazel news leave",
        "weazel news command", "weazel news high command", "weazel news management",
    ],
    "armed_forces": [
        "armed forces", "armed forces sop", "fort zancudo", "military sop", "af rules",
        "armed forces rules", "armed forces regulations", "armed forces rank",
        "armed forces command", "armed forces structure", "armed forces command structure",
        "osd", "office of the secretary of defense", "secretary of defense",
        "armed forces unicom", "unicom", "unicom strike", "af unicom",
        "armed forces vehicle", "armed forces weaponized vehicle", "military vehicle rules",
        "armed forces speed", "tank rules", "tank off base", "tank transport",
        "armed forces leo", "af leo", "af dhs", "armed forces dhs", "dohs armed forces",
        "armed forces rto", "armed forces radio", "armed forces callsign",
        "armed forces uniform", "acu", "ocp", "combat uniform", "military uniform",
        "armed forces strike", "af strike", "armed forces suspension", "armed forces blacklist",
        "armed forces transfer", "af transfer", "armed forces department transfer",
        "armed forces lockdown", "lockdown alpha", "lockdown bravo", "lockdown charlie", "lockdown delta",
        "code alpha", "code bravo", "code charlie", "code delta",
        "kos zone", "restricted area", "atc tower kos", "radio tower kos",
        "military police", "mp rules", "af mp", "gate security", "gate procedures", "cac policy",
        "armed forces iff", "identification friend or foe", "iff training",
        "armed forces cayo", "cayo perico military", "jsoc", "jsoc rules", "jsoc beard",
        "close air support", "cas rules", "armed forces cas",
        "armed forces qrf", "quick reaction force", "qrf rules",
        "armed forces la operations", "la operations military", "af la ops",
        "search and rescue af", "af s&r", "armed forces sar",
        "mortar rules", "armed forces mortar", "mortar team",
        "hard target", "soft target", "hard target soft target",
        "sam site", "sam site rp", "anti air",
        "armed forces drone", "drone rules af",
        "armed forces cam", "armed forces cac", "common access card",
        "armed forces grooming", "military grooming", "af grooming standards",
        "armed forces pmc", "pmc rules", "pmc roleplay", "private military",
        "armed forces reserves", "af reserves", "reserve guidelines",
        "fort nova", "fort nova rules", "ncis fort nova",
        "armed forces base security", "base security", "base commander",
        "armed forces customs", "military courtesy", "saluting",
        "armed forces off duty", "af off duty rp",
        "armed forces flyable", "e-5 fly", "who can fly military",
        "armed forces convoy", "af convoy", "military convoy",
        "armed forces hc", "armed forces lc", "armed forces high command",
        "vncjcos", "vcjcos", "armed forces coordinator",
        "armed forces raiding", "raiding fort zancudo",
    ],
    "sbo": [
        "sbo", "special bureau operations", "sbo sop", "sbo rules", "sbo agent",
        "sbo rank", "sbo promotion", "sbo activity", "sbo hours", "sbo loa",
        "sbo leave", "sbo strike", "sbo suspension", "sbo termination", "sbo blacklist",
        "sbo discipline", "sbo punishment", "sbo command", "sbo hc", "sbo lc",
        "sbo director", "sbo assistant director", "sbo chief of staff",
        "sbo operations director", "sbo commander", "sbo captain", "sbo lieutenant",
        "sbo special agent in charge", "sbo sac", "sbo senior special agent",
        "sbo special agent", "sbo field agent", "sbo probationary agent",
        "sbo supervisor", "sbo supervisory agent", "sbo chain of command",
        "sbo uniform", "sbo vehicle", "sbo weapon", "sbo loadout", "sbo carbine",
        "sbo unmarked", "sbo vehicle color", "sbo dispatch", "sbo self dispatch",
        "sbo rto", "sbo radio", "sbo 10 codes", "sbo miranda", "sbo phonetic",
        "sbo scene command", "sbo priority scene", "sbo non priority",
        "sbo use of force", "sbo force continuum", "sbo penal code",
        "sbo cad", "sbo identification", "sbo callsign", "sbo name format",
        "sbo dhs", "sbo dohs", "sbo homefront", "sbo training", "sbo ride along",
        "sbo meeting", "sbo attendance", "sbo weekly hours", "sbo 5 hours",
        "sbo discord", "sbo text chat", "sbo voice chat", "sbo recruitment",
        "sbo in game", "sbo roleplay rules", "sbo break character",
        "sbo code of conduct", "sbo code of ethics",
    ],
    "cartel": [
        "cartel", "cartels", "cartel sop", "cartel rules", "cartel handbook",
        "cartel coordination", "cartel coordinator", "cartel expectations",
        "cartel rank", "cartel structure", "cartel high command", "cartel low command",
        "cartel overseer", "cartel command", "cartel parole", "cartel leave",
        "cartel outfit", "cartel uniform", "cartel tactical", "shitter fit",
        "cartel raid", "cartel bog", "boots on ground cartel", "cartel life rule",
        "cartel fear rp", "cartel tier", "cartel tier 1", "cartel tier 2", "cartel tier 3",
        "cartel beef", "cartel beef stage", "cartel stage 1", "cartel stage 2", "cartel stage 3",
        "cartel kos", "cartel war", "cartel allies", "cartel turf",
        "cartel leo", "cartel traffic stop", "cartel leo raid",
        "cartel interaction", "cartel property", "cartel postal", "cartel ymap",
        "cartel street gang", "cartel vs street gang", "cartel provoke",
        "cartel name format", "cartel discord name", "cartel callsign",
        "cartel subdivision", "cartel rank slot", "cartel double slot",
        "cartel new life rule", "cartel ooc", "cartel gme", "cartel calladmin",
        "cartel gun rules", "cartel weapons", "cartel punishment",
        "madrazo", "cartel gang tag", "cartel weaponized vehicle",
        "saif cartel", "cartel manager", "cartel coordinator chain",
        "one cartel", "only one cartel", "join cartel", "how to join cartel",
    ],
    "vo": [
        "vo", "volunteer officer", "volunteer police", "vo sop", "vo rules",
        "vo callsign", "vo-", "vo charger", "vocharger", "vo uniform", "vo weapon",
        "vo vehicle", "vo plate", "cvo", "community volunteer officer",
        "vo name", "vo naming", "vo cad", "vo duty", "vo rto", "vo discord",
        "vo coordinator", "vo chain of command", "vo dohs", "vo punishment",
        "vo abuse", "vo blacklist", "vo removal", "vo permissions",
        "vo outfit", "vo outfit id", "9621", "9623",
        "volunteer officer rank", "volunteer department", "volunteer purpose",
        "dohs volunteer", "dohs pull over", "dohs violation",
        "vo showbadge", "vo viewbadge", "vo identify", "vo callsign format",
        "vo license plate", "vo plate format", "vo number",
        "vo penal code", "vo jailing", "vo jail", "vo no jail",
        "how to be a vo", "how to join vo", "new player leo",
        "vo getting on duty", "vo /duty", "vo blip", "vo headtag",
        "what is volunteer officer", "volunteer cop",
        "p. cotton", "j. rice", "ren owner", "ryan s owner",
    ],
    "gang": [
        "gang", "gangs", "gang community", "gang sop", "gang rules", "gang guidelines",
        "gang handbook", "gang management", "gang coordinator", "gang coordination",
        "gang director", "gang overseer", "gang manager", "gang command",
        "gang tier", "tier 1", "tier 2", "tier 3", "gang tiers", "fear hierarchy",
        "gang activity", "gang hours", "gang requirement", "100 hours", "gang inactivity",
        "gang shutdown", "gang strike", "gang merge", "gang merging",
        "gang rank", "gang promotion", "gang time in rank", "gang low command",
        "gang high command", "gang supervisor rank", "gang instatement",
        "gang transfer", "gang parole", "gang leave", "gang category",
        "cartel", "militia", "motorcycle club", "mc gang", "crime family", "street gang",
        "gang alliance", "gang relations", "gang rivalry", "gang beef", "beef stage",
        "beef stages", "stage 1", "stage 2", "stage 3", "gang war", "turf war",
        "kos", "kill on sight gang", "gang kos", "gang raid", "raiding",
        "boots on ground", "gang gme", "gang allies", "gang ally",
        "gang recruitment", "recruitment hub", "join a gang", "how to join gang",
        "gang parole", "gang cooldown", "gang 30 days",
        "/relations set", "/relations view", "gang relations system",
        "cartel beef", "street gang beef", "motorcycle club beef", "crime family beef",
        "gang power stacking", "cross category", "gang subdivision",
        "gang discord name", "gang prefix", "gang hash", "gang dollar sign",
        "malvados", "moretti", "accendere gang", "korean mob",
    ],
    "verified_civilian": [
        "verified civilian", "verified civ", "vc rank", "verified civilian sop",
        "verified civilian rules", "verified civilian promotion", "verified civilian hours",
        "verified civilian activity", "verified civilian headtag", "verified civilian discord",
        "verified civilian loa", "verified civilian discipline", "verified civilian strike",
        "verified civilian demotion", "verified civilian termination", "verified civilian resign",
        "verified civilian reinstatement", "verified civilian callsign",
        "verified civilian chain of command", "verified civilian command",
        "verified civilian overseer", "verified civilian manager", "verified civilian supervisor",
        "verified civilian lead manager", "verified civilian lead supervisor",
        "verified civilian hc", "verified civilian high command",
        "verified civilian event", "verified civilian photo", "verified civilian general",
        "verified civilian partnership", "verified civilian gang", "verified civilian business",
        "verified civilian fake cop", "fake cop rp", "elite class civilian", "elite class fake cop",
        "upper class civilian", "middle class civilian", "verified business", "verified gang",
        "malvados mc", "moretti crime family", "korean mob", "elite society",
        "boosted boiz", "white widow", "california aviation", "weazel news",
        "cookie corner", "cali towing", "lock and load", "strap-n taxis", "nexus transport",
        "verified civilian 24/7", "ammunation", "black woods saloon", "hayes auto",
        "hornys", "ls customs", "pops diner", "verified civilian /job",
        "new life rule civilian", "value of life", "fear for freedom",
        "gta driving civilian", "breaking character terms", "evaluate command",
        "myhours command", "/evaluate", "/myhours", "bi-weekly promotion",
        "verified civilian fake leo", "blaine county citation", "los santos public safety",
        "verified civilian headtag stolen", "steal leo vehicle",
    ],
    "bse": [
        "bse", "bureau of special enforcement", "bse agent", "bse sop", "bse rank",
        "bse promotion", "bse rules", "bse callsign", "bse-", "special agent", "field agent",
        "probationary agent", "lead special agent", "senior special agent", "special agent in charge",
        "sac", "dsac", "deputy special agent", "section chief", "chief of staff bse",
        "division chief", "regional director bse", "assistant director bse", "deputy director bse",
        "bse director", "bse command", "bse hc", "bse lc", "bse thc",
        "bse activity", "bse hours", "bse loa", "bse leave", "bse suspension", "bse discipline",
        "bse termination", "bse blacklist", "bse transfer", "bse reinstatement",
        "bse vehicle", "bse weapon", "bse uniform", "bse use of force", "bse force",
        "bse rto", "bse radio", "bse cad", "bse dispatch", "bse undercover", "bse uc",
        "bse srt", "bse tac", "bse tactical", "bse aviation", "bse air", "bse border",
        "bse traffic stop", "bse felony", "bse federal", "bse corruption", "bse corrupt",
        "bse badge", "bse naming", "bse discord name", "bse in-game name",
        "bse recruitment", "bse training", "bse academy", "bse fto",
        "bse bank robbery", "bse homicide", "bse hostage", "bse evidence",
        "bse mag dump", "bse flashbang", "bse explosive", "bse plate",
        "deklan brackford", "federal authority local impact",
        "bse high command", "bse low command", "bse supervisor",
        "bse probationary", "bse agent rank", "bse coc", "bse chain of command",
    ],
    "army": [
        "army", "us army", "united states army", "fort zancudo", "military", "soldier",
        "army sop", "army regulation", "army rank", "army promotion", "army discharge",
        "honorable discharge", "general discharge", "dishonorable discharge", "army blacklist",
        "army loa", "leave of absence army", "army activity", "army hours", "army reserve",
        "individual ready reserve", "311th reserve", "311th brigade", "army training",
        "basic combat training", "bct", "drill instructor", "army recruitment",
        "army uniform", "acu", "apfu", "asu", "army service uniform", "army combat uniform",
        "icvc", "beret army", "campaign cover", "army vehicle", "humvee", "army humvee",
        "military police", "mp corps", "26th military police", "delta force", "ocs",
        "officer candidate school", "officer candidate exam", "army officer", "warrant officer",
        "commissioned officer", "noncommissioned officer", "nco", "e-2", "e-3", "e-4", "e-5",
        "e-6", "e-7", "e-8", "e-9", "o-1", "o-2", "o-3", "o-4", "o-5", "o-6",
        "w-1", "w-2", "w-3", "w-4", "w-5", "private", "sergeant", "lieutenant", "colonel",
        "brigadier general", "army general", "army hq", "army headquarters",
        "army command", "army internal affairs", "army ia", "army strike", "army suspension",
        "army discharge outcome", "army enlist", "common access card", "cac", "gate duty",
        "army aviation", "army aircraft", "army pilot", "army flight", "1st cavalry",
        "army corps", "army division", "army structure", "army core values",
        "army loa policy", "army investigation", "army ui",
    ],
    "accendere": [
        "accendere", "accendere corp", "accendere corporation", "militia", "light riders",
        "supreme commander", "deputy commander", "chief of operations", "chief of intelligence",
        "chief of logistics", "operations commander", "field commander", "unit commander",
        "station commander", "division commander", "squad leader", "senior operator", "operator",
        "accendere rank", "accendere promotion", "accendere rules", "accendere sop",
        "accendere weapon", "accendere gun", "accendere vehicle", "accendere uniform",
        "accendere activity", "accendere hours", "accendere disciplinary", "accendere strike",
        "accendere location", "accendere war", "gang war accendere", "accendere recruit",
        "accendere command", "accendere hc", "accendere lc", "accendere discord",
        "accendere training", "accendere fta", "accendere bounty", "accendere security",
        "accendere drug", "accendere convoy", "accendere gang", "accendere member",
        "accendere mk2", "accendere rpg", "accendere flashbang", "accendere sniper",
        "accendere 50 cal", "accendere armored", "accendere bulletproof",
        "zancudo forest", "raton canyon", "zancudo trail", "route 15 field",
    ],
    "business": [
        "business", "businesses", "business sop", "business rules", "business guidelines",
        "business coordination", "business coordinator", "business command", "business owner",
        "business member", "business supervisor", "business hc", "business lc",
        "business application", "business hub", "business advert", "join a business",
        "business location", "business claim", "business ymap", "business resign",
        "business resignation", "business transfer", "business merge", "business partner",
        "business contract", "business partnership", "business recruitment", "business recruit",
        "business tier", "business tag", "business gangtag", "business headtag",
        "business passive", "passive business", "business violence", "business weapon",
        "business pistol", "business security", "business car club", "car club rules",
        "security business", "business promotion", "business demotion", "business cooldown",
        "business documents", "business roster", "business discord", "business vc",
        "business identifier", "business name", "business abbreviation", "business cad",
        "gruppe 6", "g6", "talon security", "council security", "vexorix", "tard r",
        "california aviation", "american trucking", "apex aviation", "white widow",
        "weazel news", "ko club", "boosted boiz", "throttle junkies", "trail blazers",
        "board of directors", "lead business coordinator", "lbc", "sbc", "tbc",
        "how many businesses", "can i join", "how to join business", "business rules calirp",
        "instatement", "business instate", "business movement", "business tier 2", "tier 3",
    ],
    "overdrive": [
        "overdrive", "od-", "car club", "car meet", "car cruise", "street racing", "street race",
        "street takeover", "drift", "drifting", "mechanic rp", "mechanic roleplay",
        "corrupt mechanic", "getaway driver", "getaway", "drug transportation", "overdrive rank",
        "overdrive promotion", "overdrive rules", "overdrive sop", "overdrive callsign",
        "overdrive uniform", "overdrive vehicle", "overdrive gme", "overdrive rto",
        "overdrive activity", "overdrive hours", "overdrive disciplinary", "overdrive chain",
        "street demon", "street terrorizer", "no hesi", "speed terrorizer", "street racer",
        "overdrive driver", "overdrive command", "nik c", "ryan overdrive", "overdrive director",
        "overdrive president", "overdrive manager", "gun certification", "overdrive weapon",
        "overdrive mechanic", "overdrive recruit", "overdrive loa", "overdrive discord",
        "overdrive flee", "overdrive leo", "overdrive pursui", "overdrive passive",
        "car enthusiast", "automotive roleplay", "overdrive founder", "overdrive foreman",
    ],
    "sahp": [
        "sahp", "highway patrol", "san andreas highway patrol", "state trooper", "trooper",
        "sahp sop", "sahp rank", "sahp promotion", "sahp cadet", "probationary cadet",
        "sahp transfer", "sahp loa", "sahp activity", "sahp vehicle", "sahp uniform",
        "sahp weapon", "sahp subdivision", "sahp reserve", "sahp disciplinary",
        "sahp chain of command", "sahp commissioner", "sahp high command", "sahp low command",
        "pit maneuver sahp", "sahp plate", "xshpx", "1s-", "2s-", "3s-", "4s-", "5s-", "6s-",
        "7s-", "8s-", "pc-", "fto sahp", "sahp training", "sahp ranks", "sahp callsign",
        "sahp radio", "sahp policy", "sahp rules", "sahp briefing", "sahp reinstatement",
        "sahp resignation", "sahp retirement", "sahp lc", "sahp hc", "sahp colonel",
        "sahp captain", "sahp lieutenant", "sahp sergeant", "sahp corporal", "sahp master trooper",
        "how to get promoted sahp", "sahp hour requirement", "sahp hours", "sahp leave",
        "sahp absence", "sahp reduced hours", "sahp internal affairs", "sahp tenure",
        "sahp miranda", "trey s", "d. ray", "josh w",
    ],
    "staff": [
        "staff", "staff punishment", "staff offense", "staff strike", "staff suspension",
        "staff demotion", "staff termination", "abuse of staff", "faking staff hours", "staff duty",
        "staff rto", "name dropping", "logging bans", "incorrect punishment", "pt", "pcd",
        "leaking ticket", "stream sniping", "staff member", "admin", "staff rule", "staff behavior",
        "staff conduct", "staff hours", "staff abuse", "staff guidelines", "unprofessional",
        "roleplaying on duty", "spectating staff", "faking hours", "fake hours", "falsify hours",
        "clock hours", "clocking hours", "fake clockin", "logging incorrect", "not logging",
    ],
}

GSOP_TEXT = '''CALIFORNIA ROLEPLAY GLOBAL STANDARD OPERATING PROCEDURES
Latest Revision: January 26th, 2026

Key Sections: Introduction, Departments Structure, In-game Rules, RTO Etiquette, 
Weapons/Uniforms/Vehicles, Transfer/Resignation, Department Policies, 
Miscellaneous Information, Any Department Policy, Jurisdictions

TABLE OF CONTENTS:
1.0 Introduction - 1.2 Mission Statement, Preliminary Information
2.0 Departments Structure - 2.1 By Category, 2.2 Chain of Command
3.0 In-game Rules - 3.1 In Character, 3.2 Duty Blips/OOC
4.0 Radio Traffic Only (RTO) - 4.1 10-Codes, 4.2 Communicating, 4.3 Authority
5.0 Weapon, Uniform, Vehicle - 5.1 General, 5.2 Vehicles, 5.3 Weapons, 5.4 Uniforms
6.0 Use of Force Continuum
7.0 Transfer, Resignation, Termination - 7.1 Transfers, 7.2 Resignation, 7.3 Termination, 7.4 Reinstatement
8.0 Department Policies - 8.1 Command, 8.2 Discipline, 8.3 Requirements, 8.4 Punishments, 8.5 Training, 8.6 Subdivisions, 8.7 LEO Traffic Stops, 8.8 Corrupt RP, 8.9 Badge Formats
9.0 Global Policies - 9.1 TAC, 9.2 Undercover, 9.3 Border, 9.4 FAA
10.0 Miscellaneous
11.0 Jurisdictions / Patrol Zones
12.0 Final Statement

GSOP OVERVIEW:
This is the official Global Standard Operating Procedures of California Roleplay effective January 26th, 2026. 
This document has been created to guide departments into growth, realism and structure. This is to be followed at all times.

KEY RULES:
- All members must follow 2-life rule in roleplay
- No breaking character unless staff initiates
- Members must follow GSOP, penal codes, use of force continuum, weapon policies
- Members under investigation cannot activate until cleared
- Members must provide consistent realistic roleplay
- Members must meet assigned duties and hour requirements
- On tactical scenes: Scene Command, Negotiator, Tac Command should be 2-3 different people
- All departments must abide by penal codes and internal punishment guidelines
- Chain of Command MUST BE FOLLOWED IN RTO AT ALL TIMES
- Departments have max 25 command spots (5 HC, 4 THC, 12 LC preferred)
- All promotion/demotion follow cooldown rules
- Transfer policies: 60 days minimum in department before transfer, one-rank demotion upon transfer
- Termination results in 1-week LEO cooldown
- Vehicle pursuits: Opposing lane discretionary, officer liable for damage
- Weapons only justified by Use of Force Continuum
- No "mag dumping" - continuous assessment required
- Flashbangs: Tactical units or tactically certified only
- LEO Supervisors can pull over own units
- Only MAIN Department HC and DHS can pull over on-duty LEOs
- Corrupt roleplay prohibited (except Syndicate Command exception for bribes)
- Members represent departments; must uphold standards and remain professional

TRANSFER STRUCTURE:
Main LEO ↔ Main LEO ✅
Main FED ↔ Main FED ✅
Pre Main ↔ Pre Main ✅
Main FED → Pre Main ✅
Any DOD ↔ Any DOD ✅
Pre Main → Main FED ❌
Any Fed → Any LEO ❌

DEPARTMENT STRIKES:
Strike #1: Lose staff clockin perms (main fed/leo only)
Strike #2: Demoted to Pre-Main or shutdown
Strike #3: Department shutdown

See CaliRP Global SOP for complete details on all sections.
'''

CIVILIAN_PUNISHMENTS = '''CALIRP CIVILIAN PUNISHMENT GUIDELINES

IN-GAME OFFENSES:
RDM: 1st Jail 900s → 2nd 12h Ban → 3rd 3d Ban
VDM: 1st Jail 900s → 2nd 12h Ban → 3rd 3d Ban
Breaking Priority Cooldown: 1st Jail 300s → 2nd Kick → 3rd 1d Ban
Mass RDM (3+): 1st 1w Ban → 2nd 2w Ban → 3rd 30d Ban
Mass VDM (3+): 1st 1w Ban → 2nd 2w Ban → 3rd 30d Ban
FailRP: 1st Kick → 2nd 2h Ban → 3rd 3d Ban
No Intent to RP: 1st Kick → 2nd 6h Ban → 3rd 3d Ban
Unrealistic Driving: 1st Jail 600s → 2nd Jail 600s → 3rd 3d Ban
Server Disrespect: 1st Kick → 2nd 3d Ban → 3rd 1w Ban
Sexual RP: 1st 3d Ban → 2nd 1w Ban → 3rd Perm Ban
Microphone Spamming: 1st Warning → 2nd Kick → 3rd 1d Ban
Interfering With RP: 1st Jail 600s → 2nd 1h Ban → 3rd 1d Ban
Ruining Livestream: 1st Kick → 2nd 1d Ban → 3rd 3d Ban
Impersonating Staff: 1st 1w Ban → 2nd 30d Ban
Harassment/Bullying: 1st 1d Ban → 2nd 3d Ban → 3rd 1w Ban
Sexual Harassment: 1st 30d Ban → 2nd Perm Ban
Derogatory Slurs: 1st 1w Ban → 2nd 2w Ban → 3rd 30d Ban
Racial Slurs: 30d Ban
Lying To Staff: 1st Kick → 2nd 1d Ban → 3rd 3d Ban
LTAP/Combat Logging: 1st 3d Ban → 2nd 1w Ban
Modding/Hacking: Permanent Ban
Terrorist Events: 1st 1m Ban → 2nd Perm Ban

IN-GAME CHAT OFFENSES:
Spamming: 1st 300s Mute → 2nd 3h Ban → 3rd 1d Ban
Death Threats: 30d Ban
Server Advertising: Permanent Ban
DDOS/Dox/SWAT: Permanent Ban (Unappealable)

DISCORD OFFENSES:
English Only: 1st Warning → 2nd 15m Mute → 3rd 6h Mute
Chat Spam: 1st Warning → 2nd 30m Mute
Racial Slurs: Permanent Ban
Homophobic Slurs: 1st 12h Mute → 2nd 1d Mute → 3rd 3d Mute
NSFW Content: Permanent Ban
Death Threats: 30d Ban
DDOS/Dox/SWAT: Permanent Ban (Unappealable)
Server Advertisement: Permanent Ban
Server Disrespect: 1st 3h Mute → 2nd Perm Ban
Personal Information Leak: Permanent Ban (Unappealable)
'''

PILOTS_LICENSE = '''CALIRP PILOTS LICENSE & VEHICLE ROSTER

GENERAL RULES:
Min altitude: 500ft planes, 150ft helicopters
Cannot fly over: Prisons, police impounds, military bases, government areas
Can use: Commercial runways with permission
Can land: Realistic locations (fields, paved grounds)
No firing: Unless engaged first
No crash landings: Into high RP zones
No engine failure RP: In dangerous areas
Must land: When requested by DHS/STAFF/HIGH COMMAND
Flying is passive: For civs (LEO/Gangs allowed for non-passive if realistic)
No ramming: Aircraft
No jank flying: Or unrealistic flying
Terrorism: While flying = ban

LEO RULES:
Can land: Roads, paved ground, drop off TAC on roofs
Cannot shoot: Soft targets
Open fire: Only if engaged first
TAC units: Can shoot to disable armored/BP vehicles
Fort Zancudo: Request clearance via radio 149

WEATHER:
Civs/Gangs: Any weather but must RP it
LEO: Cannot fly in unsafe (lightning, heavy fog)

RADIO:
Civs/Gangs: In-game radio 150
LEO: RTO marked as Air-Unit

AIRCRAFT:
Helicopters: Buzzard, Frogger, Maverick, Supervolito, Swift, Volatus
Single Prop: Cuban 800, Dodo, Mammatus, Velum
Twin Jet: Luxor, Nimbus, Shamal, Vestra
Cargo: Cargoplane, Cargobob2
Passenger: Jet
Special: Duster (farming only)

PUNISHMENTS:
Unrealistic Flying: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
No-Fly Zones: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
Wrong Altitude: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
Wrong Landing: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
Unauthorized Fire: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
Unsafe Weather: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
Wrong Radio: 1st Warning → 2nd 24h Strip → 3rd 14d Strip → 4th 30d Strip → 5th Revoked
Terrorist Flying: 1st 2w Ban → 2nd 1m Ban → 3rd Perm Ban
Crash Landing: 1st 3d Strip → 2nd 14d Strip → 3rd Revoked
'''

NSB_PROMOTIONS = '''CALIFORNIA ROLEPLAY - NATIONAL SECURITY BUREAU
PROMOTION & ACTIVITY GUIDELINES

CRITICAL RULES:
NEVER ask for promotion = IMMEDIATE STRIKE
Repeated requests/DMs = TERMINATION FROM NSB
Breaking chain of command = STRIKE + 2-WEEK RANK LOCK

GENERAL INFORMATION:
Promotions evaluated and announced every Sunday
Can open evaluation ticket after Sunday (before midnight)
Activity counted by hours (including minutes) for whole week
All promotions follow Global SOP cooldown rules:
- One-rank promotion = ONE WEEK cooldown
- Two-rank promotion = TWO WEEK cooldown
High Command may delay promotion if you need more time
If promotion not received but requirements met, open Evaluation Ticket

PROMOTION REQUIREMENTS BY RANK:

Probationary Agent → Patrol Agent I
Requirements:
  - 5 hours activity minimum
  - 1 week in rank minimum
  - No punishment violations past 1 week

Patrol Agent I → Patrol Agent II
Requirements:
  - 5 hours activity minimum
  - 1 week in rank minimum
  - No punishment violations past 1 week

Patrol Agent II → Senior Patrol Agent
Requirements:
  - 6 hours activity minimum
  - 1 week in rank minimum
  - No punishment violations past 1 week

Senior Patrol Agent → Supervisor I
Requirements:
  - 9 hours activity minimum
  - 1 week in rank minimum
  - Host 2 thirty-minute (30 min) recruitments
  - No punishment violations past 1 week

Supervisor I → Supervisor II
Requirements:
  - 10 hours activity minimum
  - 1 week in rank minimum
  - Host 1 training session
  - Host 2 thirty-minute (30 min) recruitments
  - No punishment violations past 1 week

Supervisor II → Head Supervisor
Requirements:
  - 10 hours activity minimum
  - 1 week in rank minimum
  - Host 1 training session
  - Host 2 thirty-minute (30 min) recruitments
  - No punishment violations past 1 week

Head Supervisor → Agent Of Administration
Requirements:
  - 10 hours activity minimum
  - 1 week in rank minimum
  - Host 1 training session
  - Host 2 thirty-minute (30 min) recruitments
  - No punishment violations past 1 week

Agent Of Administration → Agent Of Operations (TLC)
Requirements:
  - 15 hours activity minimum
  - 1 week in rank minimum
  - Host 2 training sessions
  - Host 2 thirty-minute (30 min) recruitments
  - No punishment violations past 1 week

Agent Of Operations (TLC) → Assistant Chief Of Operations (LC+)
Requirements:
  - High Command Discretion (no fixed requirements)
  - At this rank, HC determines readiness case-by-case
'''

STAFF_PUNISHMENTS = '''CALIFORNIA ROLEPLAY STAFF PUNISHMENT GUIDELINES

All outlined offences and punishments in this document follow punishment in different circumstances dependant on the situation.

STAFF OFFENSES:
Abuse of Staff Permissions: 1st Warning/Strike → 2nd Strike/Suspension → 3rd Termination
Roleplaying While on Staff Duty: 1st Strike → 2nd Suspension → 3rd Termination
Disrespecting Staff Members/Players: 1st Warning/Strike → 2nd Demotion → 3rd Termination
Faking Staff Hours: 1st Strike/Suspension → 2nd Termination
Arguing in Voice Chats: 1st Warning → 2nd Strike/Suspension → 3rd Demotion
Arguing in General Chat: 1st Warning → 2nd Strike/Suspension → 3rd Demotion
Unprofessionalism in General Chat: 1st Warning/Strike → 2nd Suspension → 3rd Demotion
Asking for a Promotion: 1st Warning → 2nd Strike/Suspension → 3rd Demotion
Not Following Chain of Command: 1st Warning → 2nd Strike → 3rd Demotion
Jank Roleplay (VDM, RDM, FailRP, etc.): 1st Warning/Strike → 2nd Suspension & Demotion → 3rd Termination
Ruining a Livestream/Stream Sniping: 1st Strike → 2nd Suspension & Demotion → 3rd Termination
Spectating On Duty Staff Members: 1st Warning → 2nd Strike/Suspension → 3rd Demotion
Not Logging Bans: 1st Warning → 2nd Strike → 3rd Demotion
Administering Incorrect Punishments: 1st Warning → 2nd Strike → 3rd Suspension & Demotion
Complaining About PT/PCD: 1st Warning → 2nd Strike → 3rd Demotion
OOC Name Dropping: 1st Strike → 2nd Suspension → 3rd Demotion
Lying to Staff: 1st Warning/Strike → 2nd Strike/Demotion → 3rd Termination
Breaking Staff RTO: 1st Warning → 2nd Strike/Suspension → 3rd Suspension & Demotion
Harassment: 1st Strike → 2nd Suspension & Demotion → 3rd Termination
Leaking Ticket Information: 1st Strike → 2nd Suspension & Demotion → 3rd Termination
'''

LEO_PUNISHMENTS = '''CALIRP LEO MEMBER PUNISHMENT GUIDELINES

All punishments are logged and tracked in Discord to ensure the correct offence is given.
Going beyond the 4th offence can enforce a harsher punishment or even a blacklist from LEO roleplay.
Punishment Categories: Warning, Suspension, Light Suspension, Hard Suspension, Temp Blacklist, Perm Blacklist

MEMBER OFFENSES:
No Badge in RTO: 1st Warning → 2nd 12-24 Hour Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Violating Vehicle/Outfit Guidelines: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Meta-Gaming: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th Termination
Low Effort RP: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th Termination
Not Following Recruitment Guide: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Fail-RP: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th Termination
Power Gaming: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th Termination
Abuse of BP Vehicles: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
No Fear RP: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th Termination
Breaking BOG/ROE: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Violating Gun Rules: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Excessive Use of Force: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Insubordination: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Unprofessional Behavior: 1st Warning → 2nd 1 Day Dept Suspension → 3rd 3 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Failure to Follow Life Rules: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th 7 Day Suspension/Demotion
Exploiting/Abuse of Mechanics: 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Demotion → 4th Termination
No Intent To RP: 1st Warning → 2nd 2 Day Dept Suspension/Strike → 3rd 5 Day Suspension/Demotion → 4th Termination
Not in LEO RTO when on (5+ mins): 1st Warning → 2nd 2 Day Dept Suspension → 3rd 5 Day Suspension/Strike → 4th 7 Day Suspension/Demotion
Corruption: 1st Termination → 2nd 30 Day Blacklist → 3rd 30 Day Global Blacklist → 4th Perm Blacklist
Poaching: 1st 30 Day Blacklist → 2nd 60 Day Blacklist → 3rd Perm Blacklist → 4th Perm Blacklist
Nuking Discord/Documents: Global Ban (all offences)
'''

def _build_codes_dict():
    codes = {}
    for line in CODES_AND_ALPHABET.splitlines():
        m = re.match(r'^((?:10|11)-\d+|CODE \d+|SIGNAL \d+)\s+-\s+(.+)', line.strip())
        if m:
            codes[m.group(1).upper()] = m.group(2).strip()
    return codes

CODES_DICT = _build_codes_dict()
RESPONSE_CACHE = load_cache()
CONVERSATION_HISTORY = []
MAX_HISTORY = 6

_DOC_DEFAULTS = {
    "gsop": GSOP_TEXT, "civilian": CIVILIAN_PUNISHMENTS,
    "pilots": PILOTS_LICENSE, "nsb": NSB_PROMOTIONS,
    "codes": CODES_AND_ALPHABET, "staff": STAFF_PUNISHMENTS, "leo": LEO_PUNISHMENTS,
    "sahp": "", "overdrive": "", "business": "", "accendere": "", "army": "",
    "bse": "", "verified_civilian": "", "gang": "", "vo": "", "cartel": "",
    "sbo": "", "armed_forces": "", "weazel_news": "", "talon_security": "",
    "ncea": "", "sbpd": "", "satf": "", "safr": "", "metro": "", "bb": "", "rhpd": "",
}
_DOC_FILES = {
    "gsop": "gsop.txt", "civilian": "civilian.txt",
    "pilots": "pilots.txt", "nsb": "nsb.txt",
    "codes": "codes.txt", "staff": "staff.txt", "leo": "leo.txt",
    "sahp": "sahp.txt", "overdrive": "overdrive.txt", "business": "business.txt",
    "accendere": "accendere.txt", "army": "army.txt", "bse": "bse.txt",
    "verified_civilian": "verified_civilian.txt", "gang": "gang.txt",
    "vo": "vo.txt", "cartel": "cartel.txt", "sbo": "sbo.txt",
    "armed_forces": "armed_forces.txt",
    "weazel_news": "weazel_news.txt",
    "talon_security": "talon_security.txt",
    "ncea": "ncea.txt",
    "sbpd": "sbpd.txt",
    "satf": "satf.txt",
    "safr": "safr.txt",
    "metro": "metro.txt",
    "bb": "bb.txt",
    "rhpd": "rhpd.txt",
}

def _load_docs():
    loaded = {}
    for key, filename in _DOC_FILES.items():
        path = os.path.join(DOCS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded[key] = f.read()
        except FileNotFoundError:
            loaded[key] = _DOC_DEFAULTS[key]
    return loaded

LOADED_DOCS = _load_docs()

def direct_lookup(question):
    m = re.search(r'\b((?:10|11)-\d+|CODE \d+|SIGNAL \d+)\b', question.upper())
    if m and m.group(1) in CODES_DICT:
        return f"{m.group(1)} = {CODES_DICT[m.group(1)]}"
    return None

DOC_MAP = {
    "gsop":         ("=== DOCUMENT 1: GLOBAL STANDARD OPERATING PROCEDURES (GSOP) ===",    LOADED_DOCS["gsop"]),
    "civilian":     ("=== DOCUMENT 2: CIVILIAN PUNISHMENT GUIDELINES ===",                  LOADED_DOCS["civilian"]),
    "pilots":       ("=== DOCUMENT 3: PILOTS LICENSE & VEHICLE ROSTER ===",                 LOADED_DOCS["pilots"]),
    "nsb":          ("=== DOCUMENT 4: NSB PROMOTION GUIDELINES & TRAINING PROTOCOL ===",     LOADED_DOCS["nsb"]),
    "codes":        ("=== DOCUMENT 6: 10-CODES AND NATO PHONETIC ALPHABET ===",             LOADED_DOCS["codes"]),
    "staff":        ("=== DOCUMENT 7: STAFF PUNISHMENT GUIDELINES ===",                     LOADED_DOCS["staff"]),
    "leo":          ("=== DOCUMENT 8: LEO MEMBER PUNISHMENT GUIDELINES ===",                LOADED_DOCS["leo"]),
    "sahp":         ("=== DOCUMENT 9: SAHP STANDARD OPERATING PROCEDURES ===",             LOADED_DOCS["sahp"]),
    "overdrive":    ("=== DOCUMENT 10: OVERDRIVE STANDARD OPERATING PROCEDURES ===",       LOADED_DOCS["overdrive"]),
    "business":     ("=== DOCUMENT 11: CALIRP BUSINESSES STANDARD OPERATING PROCEDURES ===", LOADED_DOCS["business"]),
    "accendere":    ("=== DOCUMENT 12: ACCENDERE CORPORATION OPERATIONS MANUAL ===",        LOADED_DOCS["accendere"]),
    "army":         ("=== DOCUMENT 13: US ARMY UNIFORM CODE OF MILITARY JUSTICE ===",       LOADED_DOCS["army"]),
    "bse":          ("=== DOCUMENT 14: BUREAU OF SPECIAL ENFORCEMENT SOP ===",              LOADED_DOCS["bse"]),
    "verified_civilian": ("=== DOCUMENT 15: VERIFIED CIVILIAN SOP ===",                    LOADED_DOCS["verified_civilian"]),
    "gang":          ("=== DOCUMENT 16: GANG COMMUNITY HANDBOOK ===",                       LOADED_DOCS["gang"]),
    "vo":            ("=== DOCUMENT 17: VOLUNTEER OFFICER SOP ===",                         LOADED_DOCS["vo"]),
    "cartel":        ("=== DOCUMENT 18: CARTEL HANDBOOK ===",                               LOADED_DOCS["cartel"]),
    "sbo":           ("=== DOCUMENT 19: SPECIAL BUREAU OPERATIONS SOP ===",                 LOADED_DOCS["sbo"]),
    "armed_forces":  ("=== DOCUMENT 20: ARMED FORCES STANDARD OPERATING PROCEDURES ===",   LOADED_DOCS["armed_forces"]),
    "weazel_news":   ("=== DOCUMENT 21: WEAZEL NEWS STANDARD OPERATING PROCEDURES ===",    LOADED_DOCS["weazel_news"]),
    "talon_security": ("=== DOCUMENT 22: TALON SECURITY STANDARD OPERATING PROCEDURES ===", LOADED_DOCS["talon_security"]),
    "ncea":           ("=== DOCUMENT 23: NATIONAL CRIMINAL ENFORCEMENT AGENCY (NCEA) SOP ===", LOADED_DOCS["ncea"]),
    "sbpd":           ("=== DOCUMENT 24: SOUTH BEACH POLICE DEPARTMENT (SBPD) SOP ===",      LOADED_DOCS["sbpd"]),
    "satf":           ("=== DOCUMENT 25: SAN ANDREAS TASK FORCE (SATF) SOP ===",            LOADED_DOCS["satf"]),
    "safr":           ("=== DOCUMENT 26: SAFR / EMS STANDARD OPERATING PROCEDURES ===",    LOADED_DOCS["safr"]),
    "metro":          ("=== DOCUMENT 27: METRO POLICE DEPARTMENT (MPD) SOP ===",           LOADED_DOCS["metro"]),
    "bb":             ("=== DOCUMENT 28: BOOSTED BOIZ (BB) STANDARD OPERATING PROCEDURES ===", LOADED_DOCS["bb"]),
    "rhpd":           ("=== DOCUMENT 29: RHPD MASTER ROSTER & SOP (ROCKFORD HILLS POLICE DEPARTMENT) ===", LOADED_DOCS["rhpd"]),
}

DOC_LABELS = {
    "gsop":         "General Rules & GSOP",
    "civilian":     "Civilian Punishments",
    "pilots":       "Pilots License & Aviation",
    "nsb":          "NSB Promotion Requirements & Training Protocol",
    "codes":        "10-Codes & NATO Alphabet",
    "staff":        "Staff Punishments",
    "leo":          "LEO Member Punishments",
    "sahp":         "SAHP Standard Operating Procedures",
    "overdrive":    "Overdrive Car Club SOP",
    "business":     "CaliRP Businesses SOP",
    "accendere":    "Accendere Corporation Operations Manual",
    "army":         "US Army UCMJ & Regulations",
    "bse":          "Bureau of Special Enforcement SOP",
    "verified_civilian": "Verified Civilian SOP",
    "gang":          "Gang Community Handbook",
    "vo":            "Volunteer Officer SOP",
    "cartel":        "Cartel Handbook",
    "sbo":           "Special Bureau Operations SOP",
    "armed_forces":  "Armed Forces Standard Operating Procedures",
    "weazel_news":   "Weazel News Standard Operating Procedures",
    "talon_security": "Talon Security Standard Operating Procedures",
    "ncea":           "National Criminal Enforcement Agency (NCEA) SOP",
    "sbpd":           "South Beach Police Department (SBPD) SOP",
    "satf":           "San Andreas Task Force (SATF) SOP",
    "safr":           "SAFR / EMS Standard Operating Procedures",
    "metro":          "Metro Police Department (MPD) SOP",
    "bb":             "Boosted Boiz (BB) Standard Operating Procedures",
    "rhpd":           "RHPD Master Roster & SOP (RockFord Hills Police Department)",
}

def get_relevant_documents(question):
    q = question.lower()
    return [doc for doc, kws in DOCUMENT_KEYWORDS.items() if any(kw in q for kw in kws)]

def ask_clarification(matched_docs):
    options = matched_docs if matched_docs else list(DOC_LABELS.keys())
    if not matched_docs:
        print("\n🤔 I'm not sure which area that relates to. Which one are you asking about?")
    else:
        print(f"\n🤔 That could relate to a few areas. Which one specifically?")
    for i, key in enumerate(options, 1):
        print(f"  {i}. {DOC_LABELS.get(key, key.upper())}")
    while True:
        choice = input("> ").strip().lower()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return [options[int(choice) - 1]]
        for key in options:
            if choice == key or choice == DOC_LABELS.get(key, "").lower():
                return [key]
        print(f"  Enter a number between 1 and {len(options)}.")

def build_context(relevant_docs):
    return "\n\n".join(f"{DOC_MAP[d][0]}\n{DOC_MAP[d][1]}" for d in relevant_docs if d in DOC_MAP)

def ask_claude(context, question, relevant_docs):
    system_content = (
        "You are a CaliRP Rules Assistant. Find and return accurate information from the provided documents.\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. READ every line carefully\n"
        "2. For rank progressions, find EXACT rank the user asks about\n"
        "3. Return ONLY requirements under that exact rank progression\n"
        "4. DO NOT mix up adjacent ranks\n"
        "5. Quote exact requirements from document\n"
        "6. Double-check you have correct rank before answering\n"
        "7. Cite exact section/rank name\n"
        "8. IF USER ASKS FOR 'ALL' CODES/LISTS: Return the COMPLETE list from the document\n"
        "9. Do NOT truncate or give examples when user asks for complete lists\n"
        "10. If answer not found, say clearly"
    )
    user_content = f"DOCUMENTS ({', '.join(d.upper() for d in relevant_docs)}):\n{context}\n\nQUESTION: {question}"
    history = CONVERSATION_HISTORY[-MAX_HISTORY:]
    messages = history + [{"role": "user", "content": user_content}]
    try:
        print("\n🤖 Claude:\n", end="", flush=True)
        full_response = []
        with _claude_client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system_content,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_response.append(text)
        answer = "".join(full_response)
        CONVERSATION_HISTORY.append({"role": "user", "content": question})
        CONVERSATION_HISTORY.append({"role": "assistant", "content": answer})
        RESPONSE_CACHE[question.lower().strip()] = answer
        save_cache()
        print("\n")
    except Exception as e:
        print("\n❌ Error:", e)

def main():
    print("=" * 75)
    print("  🚔 CaliRP Global Q&A | Claude (claude-haiku-4-5) | COMPLETE VERSION")
    print("  Docs: GSOP + Civilian + Pilots + NSB + 10-Codes + Staff + LEO + SAHP + Overdrive + Business + Accendere + Army + BSE + Verified Civilian + Gang + VO + Cartel + SBO + Armed Forces + Weazel News + Talon Security + NCEA + SBPD + SATF + SAFR + Metro + BB + RHPD")
    print("=" * 75)
    print("\n📚 DOCUMENTS:")
    for i, label in enumerate([
        "GSOP - Global Standard Operating Procedures (complete)",
        "CIVILIAN PUNISHMENTS - Full punishment guidelines",
        "PILOTS LICENSE - Aviation rules & vehicles",
        "NSB - Rank promotion, activity requirements, training & protocol",
        "10-CODES & NATO - Radio codes and phonetic alphabet",
        "STAFF PUNISHMENTS - Staff offense guidelines",
        "LEO PUNISHMENTS - LEO member offense guidelines",
        "SAHP SOP - San Andreas Highway Patrol Standard Operating Procedures",
        "OVERDRIVE SOP - Overdrive Car Club Standard Operating Procedures",
        "BUSINESS SOP - CaliRP Businesses Standard Operating Procedures",
        "ACCENDERE - Accendere Corporation Operations Manual",
        "ARMY - US Army Uniform Code of Military Justice & Regulations",
        "BSE - Bureau of Special Enforcement Standard Operating Procedures",
        "VERIFIED CIVILIAN - Verified Civilian Standard Operating Procedures",
        "GANG - Gang Community Handbook",
        "VO - Volunteer Officer Standard Operating Procedures",
        "CARTEL - Cartel Handbook",
        "SBO - Special Bureau Operations Standard Operating Procedures",
        "ARMED FORCES - Armed Forces Standard Operating Procedures",
        "WEAZEL NEWS - Weazel News Standard Operating Procedures",
        "TALON SECURITY - Talon Security Standard Operating Procedures",
        "NCEA - National Criminal Enforcement Agency Standard Operating Procedures",
        "SBPD - South Beach Police Department Standard Operating Procedures",
        "SATF - San Andreas Task Force Standard Operating Procedures",
        "SAFR - EMS / Fire & Rescue Standard Operating Procedures",
        "METRO - Metro Police Department Standard Operating Procedures",
        "BB - Boosted Boiz Standard Operating Procedures",
        "RHPD - Redwood Hills Police Department Master Roster",
    ], 1):
        print(f"  {i}. {label}")
    print("\nCOMMANDS:\n  'list' - Show documents  |  'clear' - Reset conversation  |  'quit' - Exit\n")
    print("-" * 75)

    while True:
        user_input = input("\n❓ Question:\n> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 Goodbye!")
            break
        if user_input.lower() == "list":
            print("\n📚 DOCUMENTS: GSOP | Civilian | Pilots | NSB | 10-Codes | Staff | LEO | SAHP | Overdrive | Business | Accendere | Army | BSE | Verified Civilian | Gang | VO | Cartel | SBO | Armed Forces | Weazel News | Talon Security | NCEA | SBPD | SATF | SAFR | Metro | BB | RHPD\n")
            continue
        if user_input.lower() == "clear":
            CONVERSATION_HISTORY.clear()
            print("\n🔄 Conversation history cleared.\n")
            continue
        hit = direct_lookup(user_input)
        if hit:
            print(f"\n⚡ Instant: {hit}\n")
            print("-" * 75)
            continue
        cache_key = user_input.lower().strip()
        if cache_key in RESPONSE_CACHE:
            print(f"\n💾 Cached:\n{RESPONSE_CACHE[cache_key]}\n")
            print("-" * 75)
            continue
        relevant = get_relevant_documents(user_input)
        if len(relevant) == 0 or len(relevant) >= 3:
            relevant = ask_clarification(relevant)
        context = build_context(relevant)
        print(f"\n🔍 Using: {', '.join(d.upper() for d in relevant)}")
        print("⏳ Searching...", flush=True)
        ask_claude(context, user_input, relevant)
        print("-" * 75)

if __name__ == "__main__":
    main()
