"""
US News Radar — source registry.
~200 American news sources: national + regional (all 50 states represented).
Each source: name, url, backup_url?, category, lean, is_regional, region, states.
"""

def _gn(site: str, q: str = "") -> str:
    """Build a Google News RSS URL for a site."""
    query = f"site:{site}" + (f"+{q.replace(' ', '+')}" if q else "")
    return f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


SOURCES = [
    # ══════════════════════════════════════════════════════════════════════════
    # NATIONAL — Wire Services
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Associated Press",       "url": "https://rsshub.app/apnews/topics/apf-topnews",      "backup_url": _gn("apnews.com"),          "category": "wire",       "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "Reuters US",             "url": _gn("reuters.com", "US news"),                        "category": "wire",       "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "UPI",                    "url": "https://www.upi.com/rss/news/us_news/",              "backup_url": _gn("upi.com"),             "category": "wire",       "lean": "center",       "is_regional": False, "region": None, "states": []},

    # ══════════════════════════════════════════════════════════════════════════
    # NATIONAL — Major Newspapers
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "New York Times",         "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",   "category": "newspaper",  "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "Washington Post",        "url": "https://feeds.washingtonpost.com/rss/national",               "backup_url": "https://feeds.washingtonpost.com/rss/politics", "category": "newspaper",  "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "Wall Street Journal",    "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",            "backup_url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",   "category": "newspaper",  "lean": "center-right", "is_regional": False, "region": None, "states": []},
    {"name": "USA Today",              "url": "https://rssfeeds.usatoday.com/usatoday-NewsTopStories",       "backup_url": _gn("usatoday.com"),        "category": "newspaper",  "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "Los Angeles Times",      "url": "https://www.latimes.com/rss2.0.xml",                          "backup_url": _gn("latimes.com"),         "category": "newspaper",  "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "Chicago Tribune",        "url": _gn("chicagotribune.com"),                                     "category": "newspaper",  "lean": "center",       "is_regional": False, "region": None, "states": []},

    # ══════════════════════════════════════════════════════════════════════════
    # NATIONAL — Cable / Broadcast
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "CNN",                    "url": "http://rss.cnn.com/rss/cnn_topstories.rss",          "category": "cable_news", "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "Fox News",               "url": "https://moxie.foxnews.com/google-publisher/latest.xml", "category": "cable_news", "lean": "right",        "is_regional": False, "region": None, "states": []},
    {"name": "NBC News",               "url": "https://feeds.nbcnews.com/nbcnews/public/news",       "category": "cable_news", "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "CBS News",               "url": "https://www.cbsnews.com/latest/rss/main",             "category": "cable_news", "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "ABC News",               "url": "https://abcnews.go.com/abcnews/topstories",           "category": "cable_news", "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "NPR News",               "url": "https://feeds.npr.org/1001/rss.xml",                  "category": "cable_news", "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "PBS NewsHour",           "url": "https://www.pbs.org/newshour/feeds/rss/headlines",    "category": "cable_news", "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "MSNBC",                  "url": "https://feeds.nbcnews.com/msnbc/public/news",         "category": "cable_news", "lean": "left",         "is_regional": False, "region": None, "states": []},

    # ══════════════════════════════════════════════════════════════════════════
    # NATIONAL — Magazines & Newsletters
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Politico",               "url": "https://rss.politico.com/politics-news.xml",          "category": "newsletter", "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "The Hill",               "url": "https://thehill.com/feed/",                           "category": "newsletter", "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "Axios",                  "url": "https://api.axios.com/feed/",                         "category": "newsletter", "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "The Atlantic",           "url": "https://www.theatlantic.com/feed/all/",               "category": "magazine",   "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "National Review",        "url": "https://www.nationalreview.com/feed/",                "category": "magazine",   "lean": "right",        "is_regional": False, "region": None, "states": []},
    {"name": "The New Yorker",         "url": "https://www.newyorker.com/feed/everything",           "category": "magazine",   "lean": "left",         "is_regional": False, "region": None, "states": []},
    {"name": "Vox",                    "url": "https://www.vox.com/rss/index.xml",                   "category": "magazine",   "lean": "left",         "is_regional": False, "region": None, "states": []},
    {"name": "The Economist US",       "url": "https://www.economist.com/united-states/rss.xml",     "category": "magazine",   "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "Newsweek",               "url": "https://www.newsweek.com/rss",                        "backup_url": _gn("newsweek.com"),        "category": "magazine",   "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "TIME",                   "url": "https://time.com/feed/",                              "category": "magazine",   "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "Slate",                  "url": _gn("slate.com"),                                      "category": "magazine",   "lean": "left",         "is_regional": False, "region": None, "states": []},
    {"name": "Washington Examiner",    "url": "https://www.washingtonexaminer.com/section/news.rss", "backup_url": _gn("washingtonexaminer.com"), "category": "magazine", "lean": "right",    "is_regional": False, "region": None, "states": []},
    {"name": "The Daily Beast",        "url": "https://feeds.thedailybeast.com/rss/articles",        "category": "magazine",   "lean": "left",         "is_regional": False, "region": None, "states": []},
    {"name": "HuffPost",               "url": "https://www.huffpost.com/section/front-page/feed",    "category": "magazine",   "lean": "left",         "is_regional": False, "region": None, "states": []},
    {"name": "Reason",                 "url": "https://reason.com/latest/feed/",                     "category": "magazine",   "lean": "libertarian",  "is_regional": False, "region": None, "states": []},
    {"name": "RealClearPolitics",      "url": "https://feeds.feedburner.com/realclearpolitics/qlMj", "category": "aggregator", "lean": "center-right", "is_regional": False, "region": None, "states": []},
    {"name": "Bloomberg",              "url": _gn("bloomberg.com", "US"),                            "category": "newspaper",  "lean": "center",       "is_regional": False, "region": None, "states": []},
    {"name": "ProPublica",             "url": "https://www.propublica.org/feeds/propublica/main",    "category": "nonprofit",  "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "The Intercept",          "url": "https://theintercept.com/feed/?rss",                  "category": "nonprofit",  "lean": "left",         "is_regional": False, "region": None, "states": []},

    # ══════════════════════════════════════════════════════════════════════════
    # NATIONAL — Think Tanks
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Brookings Institution",      "url": "https://www.brookings.edu/feed/",                     "category": "think_tank", "lean": "center-left",  "is_regional": False, "region": None, "states": []},
    {"name": "CATO Institute",             "url": "https://www.cato.org/rss/recent-opeds",               "category": "think_tank", "lean": "libertarian",  "is_regional": False, "region": None, "states": []},
    {"name": "Heritage Foundation",        "url": "https://www.heritage.org/rss/all-research-and-commentary", "category": "think_tank", "lean": "right", "is_regional": False, "region": None, "states": []},
    {"name": "Center for American Progress","url": "https://www.americanprogress.org/feed/",             "category": "think_tank", "lean": "left",         "is_regional": False, "region": None, "states": []},
    {"name": "American Enterprise Institute","url": "https://www.aei.org/feed/",                         "category": "think_tank", "lean": "center-right", "is_regional": False, "region": None, "states": []},

    # ══════════════════════════════════════════════════════════════════════════
    # NATIONAL — Google News topic feeds (broad coverage)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "GNews – US Headlines",   "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",  "category": "aggregator", "lean": "mixed", "is_regional": False, "region": None, "states": []},
    {"name": "GNews – Economy",        "url": "https://news.google.com/rss/search?q=US+economy+jobs+inflation+tariffs+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "aggregator", "lean": "mixed", "is_regional": False, "region": None, "states": []},
    {"name": "GNews – Healthcare",     "url": "https://news.google.com/rss/search?q=healthcare+medicaid+medicare+hospitals+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "aggregator", "lean": "mixed", "is_regional": False, "region": None, "states": []},
    {"name": "GNews – Immigration",    "url": "https://news.google.com/rss/search?q=immigration+border+deportation+ICE+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "aggregator", "lean": "mixed", "is_regional": False, "region": None, "states": []},
    {"name": "GNews – Climate",        "url": "https://news.google.com/rss/search?q=climate+environment+EPA+wildfires+flooding+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "aggregator", "lean": "mixed", "is_regional": False, "region": None, "states": []},
    {"name": "GNews – Technology",     "url": "https://news.google.com/rss/search?q=technology+AI+silicon+valley+big+tech+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "aggregator", "lean": "mixed", "is_regional": False, "region": None, "states": []},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — NORTHEAST (ME, NH, VT, MA, RI, CT)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Boston Globe",           "url": _gn("bostonglobe.com"),                                "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Northeast",   "states": ["MA"]},
    {"name": "Boston Herald",          "url": "https://www.bostonherald.com/feed/",                  "backup_url": _gn("bostonherald.com"), "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Northeast", "states": ["MA"]},
    {"name": "WBUR Boston",            "url": "https://www.wbur.org/rss/news",                       "category": "reg_broadcast", "lean": "center-left",  "is_regional": True, "region": "Northeast",   "states": ["MA"]},
    {"name": "Providence Journal",     "url": _gn("providencejournal.com"),                          "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Northeast",   "states": ["RI"]},
    {"name": "Rhode Island Current",   "url": "https://rhodeislandcurrent.com/feed/",                "backup_url": _gn("rhodeislandcurrent.com"), "category": "reg_nonprofit", "lean": "center", "is_regional": True, "region": "Northeast", "states": ["RI"]},
    {"name": "Hartford Courant",       "url": _gn("courant.com"),                                    "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Northeast",   "states": ["CT"]},
    {"name": "Connecticut Mirror",     "url": "https://ctmirror.org/feed/",                          "backup_url": _gn("ctmirror.org"),        "category": "reg_nonprofit", "lean": "center", "is_regional": True, "region": "Northeast", "states": ["CT"]},
    {"name": "Portland Press Herald",  "url": "https://www.pressherald.com/feed/",                   "backup_url": _gn("pressherald.com"),     "category": "reg_newspaper", "lean": "center", "is_regional": True, "region": "Northeast", "states": ["ME"]},
    {"name": "Maine Morning Star",     "url": "https://mainemorningstar.com/feed/",                  "backup_url": _gn("mainemorningstar.com"),"category": "reg_nonprofit", "lean": "center", "is_regional": True, "region": "Northeast", "states": ["ME"]},
    {"name": "Concord Monitor",        "url": _gn("concordmonitor.com"),                             "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Northeast",   "states": ["NH"]},
    {"name": "NH Bulletin",            "url": "https://newhampshirebulletin.com/feed/",              "backup_url": _gn("newhampshirebulletin.com"), "category": "reg_nonprofit", "lean": "center", "is_regional": True, "region": "Northeast", "states": ["NH"]},
    {"name": "VTDigger",               "url": "https://vtdigger.org/feed/",                          "backup_url": _gn("vtdigger.org"),        "category": "reg_nonprofit", "lean": "center", "is_regional": True, "region": "Northeast", "states": ["VT"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — MID-ATLANTIC (NY, NJ, PA, DE, MD)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "New York Daily News",    "url": "https://www.nydailynews.com/arcio/rss/category/news/","backup_url": _gn("nydailynews.com"),     "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Mid-Atlantic", "states": ["NY"]},
    {"name": "New York Post",          "url": "https://nypost.com/feed/",                            "category": "reg_newspaper", "lean": "right",        "is_regional": True, "region": "Mid-Atlantic", "states": ["NY"]},
    {"name": "Newsday",                "url": _gn("newsday.com"),                                    "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["NY"]},
    {"name": "Philadelphia Inquirer",  "url": _gn("inquirer.com"),                                   "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Mid-Atlantic", "states": ["PA"]},
    {"name": "Pittsburgh Post-Gazette","url": "https://feeds.post-gazette.com/pg-news",              "backup_url": _gn("post-gazette.com"),    "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["PA"]},
    {"name": "PA Capital-Star",        "url": "https://www.penncapital-star.com/feed/",              "backup_url": _gn("penncapital-star.com"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["PA"]},
    {"name": "NJ.com / Star-Ledger",   "url": "https://www.nj.com/arcio/rss/category/news/",        "backup_url": _gn("nj.com"),              "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["NJ"]},
    {"name": "NJ Monitor",             "url": "https://newjerseymonitor.com/feed/",                  "backup_url": _gn("newjerseymonitor.com"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["NJ"]},
    {"name": "Baltimore Sun",          "url": _gn("baltimoresun.com"),                               "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Mid-Atlantic", "states": ["MD"]},
    {"name": "Maryland Matters",       "url": "https://www.marylandmatters.org/feed/",               "backup_url": _gn("marylandmatters.org"), "category": "reg_nonprofit", "lean": "center",      "is_regional": True, "region": "Mid-Atlantic", "states": ["MD"]},
    {"name": "Delaware Online",        "url": _gn("delawareonline.com"),                             "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["DE"]},
    {"name": "WHYY Philadelphia",      "url": "https://whyy.org/feed/",                              "backup_url": _gn("whyy.org"),            "category": "reg_broadcast", "lean": "center",       "is_regional": True, "region": "Mid-Atlantic", "states": ["PA"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — SOUTHEAST (VA, NC, SC, GA, FL, TN, AL, MS, LA, AR, KY, WV)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Miami Herald",           "url": _gn("miamiherald.com"),                                "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Southeast", "states": ["FL"]},
    {"name": "Tampa Bay Times",        "url": "https://www.tampabay.com/arcio/rss/",                 "backup_url": _gn("tampabay.com"),        "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["FL"]},
    {"name": "Orlando Sentinel",       "url": _gn("orlandosentinel.com"),                            "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["FL"]},
    {"name": "Atlanta Journal-Constitution", "url": _gn("ajc.com"),                                  "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["GA"]},
    {"name": "Georgia Recorder",       "url": "https://georgiarecorder.com/feed/",                   "backup_url": _gn("georgiarecorder.com"), "category": "reg_nonprofit", "lean": "center",      "is_regional": True, "region": "Southeast", "states": ["GA"]},
    {"name": "Charlotte Observer",     "url": _gn("charlotteobserver.com"),                          "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["NC"]},
    {"name": "NC Newsline",            "url": "https://ncnewsline.com/feed/",                        "backup_url": _gn("ncnewsline.com"),      "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["NC"]},
    {"name": "WRAL News",              "url": "https://www.wral.com/rss/news/",                      "backup_url": _gn("wral.com"),            "category": "reg_broadcast", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["NC"]},
    {"name": "SC Daily Gazette",       "url": "https://scdailygazette.com/feed/",                    "backup_url": _gn("scdailygazette.com"),  "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["SC"]},
    {"name": "Richmond Times-Dispatch","url": "https://richmond.com/search/?f=rss&t=article&c=news", "backup_url": _gn("richmond.com"),        "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Southeast", "states": ["VA"]},
    {"name": "Virginia Mercury",       "url": "https://virginiamercury.com/feed/",                   "backup_url": _gn("virginiamercury.com"), "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["VA"]},
    {"name": "Nashville Tennessean",   "url": _gn("tennessean.com"),                                 "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["TN"]},
    {"name": "Tennessee Lookout",      "url": "https://tennesseelookout.com/feed/",                  "backup_url": _gn("tennesseelookout.com"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["TN"]},
    {"name": "AL.com / Birmingham News","url": "https://www.al.com/arcio/rss/category/news/",        "backup_url": _gn("al.com"),              "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["AL"]},
    {"name": "Alabama Reflector",      "url": "https://alabamareflector.com/feed/",                  "backup_url": _gn("alabamareflector.com"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["AL"]},
    {"name": "Clarion-Ledger",         "url": _gn("clarionledger.com"),                              "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["MS"]},
    {"name": "Mississippi Today",      "url": "https://mississippitoday.org/feed/",                  "backup_url": _gn("mississippitoday.org"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["MS"]},
    {"name": "Times-Picayune",         "url": _gn("nola.com"),                                       "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["LA"]},
    {"name": "Louisiana Illuminator",  "url": "https://lailluminator.com/feed/",                     "backup_url": _gn("lailluminator.com"),   "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["LA"]},
    {"name": "Arkansas Democrat-Gazette","url": _gn("arkansasonline.com"),                            "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Southeast", "states": ["AR"]},
    {"name": "Arkansas Advocate",      "url": "https://arkansasadvocate.com/feed/",                  "backup_url": _gn("arkansasadvocate.com"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["AR"]},
    {"name": "Courier-Journal",        "url": _gn("courier-journal.com"),                            "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["KY"]},
    {"name": "Kentucky Lantern",       "url": "https://kentuckylantern.com/feed/",                   "backup_url": _gn("kentuckylantern.com"), "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["KY"]},
    {"name": "WV Gazette-Mail",        "url": _gn("wvgazettemail.com"),                              "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["WV"]},
    {"name": "WV Watch",               "url": "https://wvwatch.com/feed/",                           "backup_url": _gn("wvwatch.com"),         "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Southeast", "states": ["WV"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — MIDWEST (OH, IN, IL, MI, WI, MN, IA, MO)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Chicago Sun-Times",      "url": "https://chicago.suntimes.com/rss/index.xml",          "backup_url": _gn("chicago.suntimes.com"),"category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Midwest", "states": ["IL"]},
    {"name": "Detroit Free Press",     "url": _gn("freep.com"),                                      "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Midwest", "states": ["MI"]},
    {"name": "Michigan Advance",       "url": "https://michiganadvance.com/feed/",                   "backup_url": _gn("michiganadvance.com"), "category": "reg_nonprofit", "lean": "center-left", "is_regional": True, "region": "Midwest", "states": ["MI"]},
    {"name": "MLive",                  "url": "https://www.mlive.com/arcio/rss/category/news/",      "backup_url": _gn("mlive.com"),           "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["MI"]},
    {"name": "Cleveland.com",          "url": "https://www.cleveland.com/arcio/rss/category/news/",  "backup_url": _gn("cleveland.com"),       "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["OH"]},
    {"name": "Columbus Dispatch",      "url": _gn("dispatch.com"),                                   "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["OH"]},
    {"name": "Ohio Capital Journal",   "url": "https://ohiocapitaljournal.com/feed/",                "backup_url": _gn("ohiocapitaljournal.com"),"category": "reg_nonprofit","lean": "center",       "is_regional": True, "region": "Midwest", "states": ["OH"]},
    {"name": "Indianapolis Star",      "url": _gn("indystar.com"),                                   "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["IN"]},
    {"name": "Indiana Capital Chronicle","url": "https://indianacapitalchronicle.com/feed/",          "backup_url": _gn("indianacapitalchronicle.com"),"category": "reg_nonprofit","lean": "center","is_regional": True, "region": "Midwest", "states": ["IN"]},
    {"name": "Milwaukee Journal Sentinel","url": _gn("jsonline.com"),                                 "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["WI"]},
    {"name": "Wisconsin Watch",        "url": "https://wisconsinwatch.org/feed/",                    "backup_url": _gn("wisconsinwatch.org"), "category": "reg_nonprofit",  "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["WI"]},
    {"name": "Star Tribune",           "url": "https://www.startribune.com/local/rss/",              "backup_url": _gn("startribune.com"),     "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Midwest", "states": ["MN"]},
    {"name": "MinnPost",               "url": "https://www.minnpost.com/rss/all",                    "backup_url": _gn("minnpost.com"),        "category": "reg_nonprofit", "lean": "center-left",  "is_regional": True, "region": "Midwest", "states": ["MN"]},
    {"name": "MPR News",               "url": "https://www.mprnews.org/rss",                         "backup_url": _gn("mprnews.org"),         "category": "reg_broadcast", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["MN"]},
    {"name": "Des Moines Register",    "url": _gn("desmoinesregister.com"),                          "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["IA"]},
    {"name": "Iowa Capital Dispatch",  "url": "https://iowacapitaldispatch.com/feed/",               "backup_url": _gn("iowacapitaldispatch.com"),"category": "reg_nonprofit","lean": "center",      "is_regional": True, "region": "Midwest", "states": ["IA"]},
    {"name": "Kansas City Star",       "url": _gn("kansascity.com"),                                 "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Midwest", "states": ["MO", "KS"]},
    {"name": "St. Louis Post-Dispatch","url": _gn("stltoday.com"),                                   "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Midwest", "states": ["MO"]},
    {"name": "Missouri Independent",   "url": "https://missouriindependent.com/feed/",               "backup_url": _gn("missouriindependent.com"),"category": "reg_nonprofit","lean": "center",      "is_regional": True, "region": "Midwest", "states": ["MO"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — GREAT PLAINS (ND, SD, NE, KS, OK)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Omaha World-Herald",     "url": _gn("omaha.com"),                                      "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Great Plains", "states": ["NE"]},
    {"name": "Nebraska Examiner",      "url": "https://nebraskaexaminer.com/feed/",                  "backup_url": _gn("nebraskaexaminer.com"), "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Great Plains", "states": ["NE"]},
    {"name": "Wichita Eagle",          "url": _gn("kansas.com"),                                     "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Great Plains", "states": ["KS"]},
    {"name": "Kansas Reflector",       "url": "https://kansasreflector.com/feed/",                   "backup_url": _gn("kansasreflector.com"), "category": "reg_nonprofit", "lean": "center",        "is_regional": True, "region": "Great Plains", "states": ["KS"]},
    {"name": "Tulsa World",            "url": _gn("tulsaworld.com"),                                  "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Great Plains", "states": ["OK"]},
    {"name": "Oklahoma Watch",         "url": "https://oklahomawatch.org/feed/",                     "backup_url": _gn("oklahomawatch.org"),   "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Great Plains", "states": ["OK"]},
    {"name": "Sioux Falls Argus Leader","url": _gn("argusleader.com"),                                "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Great Plains", "states": ["SD"]},
    {"name": "SD Searchlight",         "url": "https://southdakotasearchlight.com/feed/",             "backup_url": _gn("southdakotasearchlight.com"),"category": "reg_nonprofit","lean": "center",    "is_regional": True, "region": "Great Plains", "states": ["SD"]},
    {"name": "Bismarck Tribune",       "url": _gn("bismarcktribune.com"),                             "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Great Plains", "states": ["ND"]},
    {"name": "ND Monitor",             "url": "https://northdakotamonitor.com/feed/",                 "backup_url": _gn("northdakotamonitor.com"),"category": "reg_nonprofit","lean": "center",       "is_regional": True, "region": "Great Plains", "states": ["ND"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — SOUTH (TX, NM, AZ)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Dallas Morning News",    "url": "https://www.dallasnews.com/arcio/rss/",               "backup_url": _gn("dallasnews.com"),      "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "Houston Chronicle",      "url": _gn("houstonchronicle.com"),                            "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "Austin American-Statesman","url": _gn("statesman.com"),                                 "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "San Antonio Express-News","url": _gn("expressnews.com"),                                "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "Texas Tribune",          "url": "https://www.texastribune.org/feed/",                  "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "El Paso Times",          "url": _gn("elpasotimes.com"),                                 "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "KERA News Texas",        "url": "https://www.keranews.org/rss.xml",                    "backup_url": _gn("keranews.org"),        "category": "reg_broadcast", "lean": "center",       "is_regional": True, "region": "South", "states": ["TX"]},
    {"name": "Arizona Republic",       "url": _gn("azcentral.com"),                                   "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["AZ"]},
    {"name": "Arizona Mirror",         "url": "https://azmirror.com/feed/",                          "backup_url": _gn("azmirror.com"),        "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "South", "states": ["AZ"]},
    {"name": "Albuquerque Journal",    "url": _gn("abqjournal.com"),                                  "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "South", "states": ["NM"]},
    {"name": "NM Political Report",    "url": "https://nmpoliticalreport.com/feed/",                  "backup_url": _gn("nmpoliticalreport.com"),"category": "reg_nonprofit", "lean": "center",      "is_regional": True, "region": "South", "states": ["NM"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — MOUNTAIN WEST (MT, WY, CO, UT, ID, NV)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Denver Post",            "url": "https://www.denverpost.com/feed/",                    "backup_url": _gn("denverpost.com"),      "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["CO"]},
    {"name": "Colorado Sun",           "url": "https://coloradosun.com/feed/",                       "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["CO"]},
    {"name": "CPR News",               "url": "https://www.cpr.org/feed/",                          "backup_url": _gn("cpr.org"),             "category": "reg_broadcast", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["CO"]},
    {"name": "Salt Lake Tribune",      "url": "https://www.sltrib.com/feed/",                       "backup_url": _gn("sltrib.com"),          "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "Mountain West", "states": ["UT"]},
    {"name": "Deseret News",           "url": "https://www.deseret.com/arc/outboundfeeds/rss/?outputType=xml","backup_url": _gn("deseret.com"),"category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Mountain West", "states": ["UT"]},
    {"name": "Utah News Dispatch",     "url": "https://utahnewsdispatch.com/feed/",                  "backup_url": _gn("utahnewsdispatch.com"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["UT"]},
    {"name": "Las Vegas Review-Journal","url": "https://www.reviewjournal.com/feed/",                 "backup_url": _gn("reviewjournal.com"),   "category": "reg_newspaper", "lean": "right",        "is_regional": True, "region": "Mountain West", "states": ["NV"]},
    {"name": "Nevada Independent",     "url": "https://thenevadaindependent.com/feed/",              "backup_url": _gn("thenevadaindependent.com"),"category": "reg_nonprofit","lean": "center",     "is_regional": True, "region": "Mountain West", "states": ["NV"]},
    {"name": "Billings Gazette",       "url": _gn("billingsgazette.com"),                             "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Mountain West", "states": ["MT"]},
    {"name": "Montana Free Press",     "url": "https://montanafreepress.org/feed/",                  "backup_url": _gn("montanafreepress.org"),"category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["MT"]},
    {"name": "Idaho Statesman",        "url": _gn("idahostatesman.com"),                              "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["ID"]},
    {"name": "Idaho Capital Sun",      "url": "https://idahocapitalsun.com/feed/",                   "backup_url": _gn("idahocapitalsun.com"), "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "Mountain West", "states": ["ID"]},
    {"name": "Wyoming Tribune Eagle",  "url": _gn("wyomingnews.com"),                                "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "Mountain West", "states": ["WY"]},

    # ══════════════════════════════════════════════════════════════════════════
    # REGIONAL — WEST COAST (CA, OR, WA, AK, HI)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "SF Chronicle",           "url": "https://www.sfchronicle.com/feed/sfgate/rss-feed/",   "backup_url": _gn("sfchronicle.com"),     "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "West Coast", "states": ["CA"]},
    {"name": "Sacramento Bee",         "url": _gn("sacbee.com"),                                      "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "West Coast", "states": ["CA"]},
    {"name": "San Diego Union-Tribune","url": _gn("sandiegouniontribune.com"),                         "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["CA"]},
    {"name": "OC Register",            "url": "https://www.ocregister.com/feed/",                    "backup_url": _gn("ocregister.com"),      "category": "reg_newspaper", "lean": "center-right", "is_regional": True, "region": "West Coast", "states": ["CA"]},
    {"name": "CalMatters",             "url": "https://calmatters.org/feed/",                        "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["CA"]},
    {"name": "KQED",                   "url": "https://www.kqed.org/news/feed/rss2",                 "backup_url": _gn("kqed.org"),            "category": "reg_broadcast", "lean": "center-left",  "is_regional": True, "region": "West Coast", "states": ["CA"]},
    {"name": "Seattle Times",          "url": "https://www.seattletimes.com/feed/",                  "backup_url": _gn("seattletimes.com"),    "category": "reg_newspaper", "lean": "center-left",  "is_regional": True, "region": "West Coast", "states": ["WA"]},
    {"name": "WA State Standard",      "url": "https://washingtonstatestandard.com/feed/",            "backup_url": _gn("washingtonstatestandard.com"),"category": "reg_nonprofit","lean": "center",   "is_regional": True, "region": "West Coast", "states": ["WA"]},
    {"name": "KUOW Seattle",           "url": "https://www.kuow.org/rss.xml",                        "backup_url": _gn("kuow.org"),            "category": "reg_broadcast", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["WA"]},
    {"name": "Oregonian",              "url": "https://www.oregonlive.com/arcio/rss/category/news/", "backup_url": _gn("oregonlive.com"),      "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["OR"]},
    {"name": "Oregon Capital Chronicle","url": "https://oregoncapitalchronicle.com/feed/",             "backup_url": _gn("oregoncapitalchronicle.com"),"category": "reg_nonprofit","lean": "center",   "is_regional": True, "region": "West Coast", "states": ["OR"]},
    {"name": "Anchorage Daily News",   "url": "https://www.adn.com/feed/",                          "backup_url": _gn("adn.com"),             "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["AK"]},
    {"name": "Alaska Beacon",          "url": "https://alaskabeacon.com/feed/",                      "backup_url": _gn("alaskabeacon.com"),    "category": "reg_nonprofit", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["AK"]},
    {"name": "Honolulu Star-Advertiser","url": _gn("staradvertiser.com"),                              "category": "reg_newspaper", "lean": "center",       "is_regional": True, "region": "West Coast", "states": ["HI"]},
]

# ── Metadata ───────────────────────────────────────────────────────────────────

CATEGORY_LABELS = {
    "wire":          "Wire Service",
    "newspaper":     "National Newspaper",
    "cable_news":    "Cable / Broadcast",
    "newsletter":    "Political Newsletter",
    "magazine":      "Magazine / Long-Form",
    "think_tank":    "Think Tank",
    "nonprofit":     "National Nonprofit",
    "aggregator":    "News Aggregator",
    "government":    "Government / Official",
    "reg_newspaper": "Regional Newspaper",
    "reg_broadcast": "Regional Broadcast",
    "reg_nonprofit": "Regional Nonprofit",
}

LEAN_LABELS = {
    "center":        "Center",
    "center-left":   "Center-Left",
    "center-right":  "Center-Right",
    "left":          "Left",
    "right":         "Right",
    "libertarian":   "Libertarian",
    "official":      "Official",
    "mixed":         "Mixed",
}

REGIONS = [
    "Northeast",
    "Mid-Atlantic",
    "Southeast",
    "Midwest",
    "Great Plains",
    "South",
    "Mountain West",
    "West Coast",
]
