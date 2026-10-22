"""Localized user guides and service notices."""

from pages import PAGES
from translations import tr

COPY = {
    "en": {
        "help": [
            (
                "Search words without a character",
                "Leave both character fields empty and enter a word or phrase to search dialogue across "
                "all speakers. Add characters to narrow results. Matching is literal, including spaces and "
                "case. Portraits use official character IDs; missing or ambiguous identities show a "
                "placeholder.",
            ),
            (
                "Search",
                "Enter a speaker or choose a suggestion. Leave the second character empty for all "
                "dialogue. Add a character to find names and registered aliases within the speaker’s "
                "lines. This does not identify the addressee: pronouns and omitted names may be missed. "
                "Use words in dialogue to narrow results.",
            ),
            (
                "Languages and context",
                "The header language selector changes both interface and dialogue language. You can also "
                "choose dialogue language separately in the search form. Enter keywords in the selected "
                "dialogue language; search words are not automatically translated. Korean, Chinese, "
                "Japanese and English are supported. Arrow keys and Enter select a suggestion; Escape "
                "closes the list. Expand context to read up to 100 dialogue lines on either side. Adjacent "
                "lines may belong to different branches.",
            ),
            (
                "Sharing and updates",
                "Search conditions are saved in the URL; the address can be shared or bookmarked. CN "
                "advance stories may contain spoilers; the default filter approximates Korean release "
                "coverage by matching file paths. The moon/sun button changes the theme. A new-deployment "
                "notice offers an immediate update or a 30-minute reminder; updating preserves search "
                "fields in the URL.",
            ),
            (
                "Search and results",
                "The centered search opens a separate results view. Back to search and browser history "
                "preserve the entered conditions. Reload or share a results URL to repeat the search. "
                "Motion is minimized when your device requests reduced motion.",
            ),
            (
                "Dialogue details",
                "Open the guide with the header question mark; close with Escape or Close. The small "
                "question marks beside dialogue and context show file, line, branch and revision details. "
                "Adjacent lines may belong to different branches. Filenames are source paths rather than "
                "official story titles. Searched phrases are highlighted without changing source text.",
            ),
            (
                "Keyboard and language selection",
                "Tab moves from words to speaker, mentioned character, then Search; Shift+Tab reverses the "
                "order. Use arrows and Enter in the dialogue language menu, and Escape to close it. "
                "Character names entered in another language suggest names in the selected dialogue "
                "language.",
            ),
            (
                "Result order and shared context",
                "Two-character searches prioritize matches with a nearby turn by the other character in "
                "the same branch. Each direction examines up to six text rows within 60 source lines, "
                "stopping at another speaker or branch. This is ordering evidence, not confirmation of "
                "direct address or third-person mention. Lines without a name match are not added. Nearby "
                "matches in one file and branch share context. Subtitles, narration and choices without an "
                "explicit speaker remain unnamed.",
            ),
        ],
        "privacy": [
            (
                "Requests and storage",
                "Search names, phrases, language and spoiler choices are sent to the server as URL "
                "parameters and may appear in hosting logs or shared links. The app creates no accounts "
                "or search-history database and includes no analytics or advertising scripts. Theme "
                "preference is stored in localStorage; update reminders use sessionStorage. No "
                "application cookies are set.",
            ),
            (
                "External services",
                "Vercel may process IP addresses, user agents, request URLs and timestamps under its "
                "own policies. Feedback opens an external Tally form; submitted data is governed by "
                "Tally and the form operator. No external feedback form is embedded here.",
            ),
        ],
        "terms": [
            (
                "Unofficial service",
                "This is an unofficial fan reference tool, not affiliated with the game’s creators or "
                "publishers. Results match names and registered aliases; they do not confirm forms of "
                "address or conversation partners. Missing data, parsing errors and differences between "
                "servers may affect results. Check the source and surrounding dialogue.",
            ),
            (
                "Content",
                "Game content remains the property of its respective rights holders. Search access grants "
                "no redistribution or commercial rights. The service is provided as is, without "
                "guarantees of accuracy, completeness or availability.",
            ),
        ],
        "license": [
            (
                "Code and brand",
                "Arknights Index is maintained by gamerinl10n. Public use of this website is permitted. "
                "Copying, modification, redistribution or commercial use of its own code, brand or "
                "assets requires prior permission. Game content and third-party components retain their "
                "respective rights and terms.",
            ),
            (
                "Game content",
                "Game text, characters and names belong to their respective rights holders. Text is "
                "converted from ArknightsAssets/ArknightsGamedata; portraits come from "
                "ArknightsAssets/ArknightsAssets2. Source revisions and line positions are preserved. "
                "This is an unofficial fan project.",
            ),
            (
                "Fonts and software",
                "NEXON Lv2 Gothic is copyright NEXON Korea Corporation and is bundled without "
                "modification. Personal and commercial use and embedding with this notice are "
                "permitted. Modifying font files or selling the font itself is prohibited. Chinese and "
                "Japanese use device fonts. Flask (BSD-3-Clause), Pillow and other dependencies retain "
                "their package license files. Shared UI and original font files come from the same "
                "operator’s L10ndiff.",
            ),
        ],
        "changelog": [
            ("1.0.0 · 2026-10-22", "The first baseline release of Arknights Index.")
        ],
    },
    "zh": {
        "help": [
            (
                "只搜索关键词",
                "将两个角色栏留空，输入词语或短句即可搜索所有说话者的台词。添加角色可缩小范围。按原字符串匹配，区分空格及大小写。头像按官方角色ID关联；身份不明确或无图片时显示默认图标。",
            ),
            (
                "搜索",
                "输入说话角色或从列表选择。第二个人物留空时显示该角色的全部台词；填写后搜索包含该人物姓名及已登记别名的台词。结果不代表确定的称呼或对话对象，代词和省略姓名的台词可能遗漏。可用台词中的词句进一步筛选。",
            ),
            (
                "语言与上下文",
                "顶部语言切换会同时更改界面和台词语言，搜索框中也可以单独选择台词语言。关键词需使用所选语言的原文，不会自动翻译。支持韩语、中文、日语、英语。用方向键和 Enter "
                "选择建议，Esc 关闭列表。可展开前后各最多 100 条台词，相邻内容可能属于不同分支。",
            ),
            (
                "分享与更新",
                "搜索条件写入地址，可复制链接分享或收藏。国服先行剧情可能剧透，默认范围根据韩文文件路径近似判定。月亮和太阳按钮切换主题。检测到新版会提示更新，也可选择 30 "
                "分钟后提醒；更新前会将搜索框内容保存在地址中。",
            ),
            (
                "搜索与结果",
                "首页中央的搜索框会打开独立的结果页面。返回搜索或使用浏览器历史记录时保留输入条件。刷新或分享结果链接可重复搜索。设备开启减少动态效果后，将尽量减少动画。",
            ),
            (
                "台词详情",
                "点击顶部问号打开使用说明，用 Esc "
                "或关闭按钮退出。台词及上下文旁的小问号可查看文件、行号、分支和版本，相邻台词可能属于不同分支。文件名是原始路径，并非官方剧情标题。搜索词会高亮，原文保持不变。",
            ),
            (
                "键盘与语言选择",
                "Tab 按关键词、说话角色、提及角色、搜索的顺序移动，Shift+Tab 反向移动。台词语言菜单可用方向键和 Enter 选择、Esc "
                "关闭。输入其他语言的角色名时，候选项会显示当前台词语言的对应名称。",
            ),
            (
                "结果顺序与共享上下文",
                "双角色搜索优先显示同一分支中附近有对方发言的匹配结果。每个方向最多检查原文60行内的6条文本，遇到其他说话者或分支即停止。这只是排序依据，不代表已确认直接对话或第三者提及，也不会添加不含姓名的台词。同一文件、分支中的邻近匹配共享上下文。没有明确说话者的字幕、旁白和选项不推测角色。",
            ),
        ],
        "privacy": [
            (
                "请求与存储",
                "角色名、词句、语言和先行剧情选项以 URL 参数发送至服务器，可能出现在托管日志或分享链接中。本应用不建立账号或搜索历史数据库，不包含分析及广告脚本。主题存于 "
                "localStorage，更新提醒存于 sessionStorage，不设置应用 Cookie。",
            ),
            (
                "外部服务",
                "Vercel 可能依其政策处理 IP、User-Agent、请求 URL 及时间。反馈链接打开外部 Tally 表单，提交的信息适用 Tally "
                "及表单运营者的政策；本站不嵌入该表单。",
            ),
        ],
        "terms": [
            (
                "非官方工具",
                "本站为非官方同人参考工具，与游戏制作方及发行方无官方关联。搜索仅匹配姓名及已登记别名，不确认称呼和对话对象。资料遗漏、解析错误、服务器差异和更新延迟均可能影响结果，请结合原文与上下文判断。",
            ),
            (
                "内容与服务",
                "游戏内容的权利归各权利人所有。搜索服务不授予转载或商业使用权。服务按现状提供，不保证准确性、完整性及持续可用性。",
            ),
        ],
        "license": [
            (
                "代码",
                "应用代码与品牌归 gamerinl10n 所有。允许公开使用网站；代码和资源的复制、修改、再分发等其他用途须获得许可，详见仓库 LICENSE 和 NOTICE。",
            ),
            (
                "数据与依赖",
                "游戏原文、角色和名称归各权利人所有。原始数据来自 ArknightsAssets/ArknightsGamedata，由本项目转换并标记版本及行位置。Flask 使用 "
                "BSD-3-Clause，其余依赖遵循各自许可。本站使用系统字体。",
            ),
        ],
        "changelog": [("1.0.0 · 2026-10-22", "Arknights Index 的首个基准版本。")],
    },
    "ja": {
        "help": [
            (
                "単語だけで検索",
                "両方の人物欄を空にして単語や文を入力すると、全話者の台詞を検索します。人物を追加すると絞り込めます。空白と大文字・小文字を含む文字列で一致します。画像は公式人物IDで対応し、曖昧な名前や画像がない場合は共通アイコンを表示します。",
            ),
            (
                "検索",
                "話す人物を入力するか候補から選びます。2人目を空欄にすると全台詞、入力するとその人物の名前・登録別名を含む台詞を検索します。呼称や話し相手を確定する機能ではありません。代名詞や名前の省略は見つからない場合があります。語句でも絞り込めます。",
            ),
            (
                "言語と文脈",
                "上部の言語切り替えで表示と台詞の言語が一緒に変わります。検索欄では台詞の言語だけを選べます。検索語は自動翻訳しないため、選んだ言語の原文を入力してください。韓国語・中国語・日本語・英語に対応します。方向キーと "
                "Enter で候補を選び、Esc で閉じます。文脈は前後それぞれ最大100件まで展開できます。隣接する行が別の分岐の場合もあります。",
            ),
            (
                "共有と更新",
                "検索条件はURLに反映され、リンクを共有・保存できます。中国サーバー先行ストーリーにはネタバレが含まれます。初期の公開範囲は韓国語ファイルのパスに基づく近似です。月・太陽ボタンでテーマを変更します。新バージョン通知は今すぐ更新か30分後の再通知を選べます。更新時は検索欄の内容をURLに保存します。",
            ),
            (
                "検索画面と結果画面",
                "中央の検索欄から結果画面に移動します。検索に戻るボタンやブラウザーの履歴移動でも入力条件が保持されます。結果URLの再読み込みや共有で同じ検索を開けます。端末で動きを減らす設定が有効な場合はアニメーションを抑えます。",
            ),
            (
                "台詞の詳細",
                "上部の？から使い方を開き、Escや閉じるボタンで戻ります。台詞と文脈の小さな？からファイル・行・分岐・版を確認できます。隣接する台詞が別分岐の場合もあります。ファイル名は原文パスで、正式な作品名ではありません。検索語を強調し、原文は保持します。",
            ),
            (
                "キーボードと言語選択",
                "Tabは語句、話す人物、言及する人物、検索の順に移動し、Shift+Tabは逆順です。台詞の言語メニューは方向キーとEnterで選択し、Escで閉じます。別の言語で人物名を入力しても、選んだ台詞言語の名前が候補に表示されます。",
            ),
            (
                "結果の順序と共通の文脈",
                "二人の検索では同じ分岐で相手の発言が近くにある一致を優先します。前後それぞれ原文60行以内のテキスト6行まで確認し、別の話者や分岐で止めます。直接の呼びかけや第三者への言及を確定するものではなく、名前が一致しない台詞は追加しません。同じファイル・分岐の近い一致は文脈を共有します。話者が明記されない字幕・地の文・選択肢に人物を推測して付けません。",
            ),
        ],
        "privacy": [
            (
                "リクエストと保存",
                "人物名・語句・言語・先行ストーリー設定はURLパラメータとしてサーバーに送信され、ホスティングのログや共有リンクに含まれる場合があります。アカウントや検索履歴DB、分析・広告スクリプトはありません。テーマはlocalStorage、更新の再通知はsessionStorageに保存します。アプリ独自のCookieは設定しません。",
            ),
            (
                "外部サービス",
                "Vercelは独自の方針によりIP、User-Agent、URL、時刻などを処理する場合があります。フィードバックは外部Tallyフォームを開きます。送信内容にはTallyとフォーム運営者の方針が適用され、フォーム自体は当サイトに埋め込みません。",
            ),
        ],
        "terms": [
            (
                "非公式サービス",
                "ゲーム制作・運営会社とは提携していないファン向け参考ツールです。名前と登録別名の一致を検索し、呼称や相手を確定しません。データ欠落、解析ミス、サーバー差分、更新遅延があり得ます。原文と文脈を確認してください。",
            ),
            (
                "コンテンツと提供条件",
                "ゲームの権利は各権利者に帰属します。検索の利用は再配布や商用利用の許諾を意味しません。サービスは現状のまま提供され、正確性・完全性・継続利用を保証しません。",
            ),
        ],
        "license": [
            (
                "コード",
                "アプリのコードとブランドはgamerinl10nに帰属します。公開サイトの利用は可能ですが、コードや資産の複製・改変・再配布などには許可が必要です。リポジトリのLICENSEとNOTICEを参照してください。",
            ),
            (
                "データと依存関係",
                "ゲーム本文・人物・名称の権利は各権利者に帰属します。原データはArknightsAssets/ArknightsGamedataから取得し、本プロジェクトが変換して版と行位置を表示します。FlaskはBSD-3-Clause、他の依存関係は各ライセンスに従います。システムフォントを使用しています。",
            ),
        ],
        "changelog": [
            ("1.0.0 · 2026-10-22", "Arknights Indexの最初の基準バージョンです。")
        ],
    },
}


def get_page(page, ui):
    if ui == "ko":
        return PAGES[page]
    return {
        "title": tr(ui, page),
        "subtitle": "",
        "sections": [
            {"title": title, "paragraphs": [text]} for title, text in COPY[ui][page]
        ],
    }
