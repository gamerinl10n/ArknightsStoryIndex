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
                "The header language sets the main result language. Search words across Korean, Chinese, Japanese and English. "
                "Enter a word in any supported "
                "language; search words are not automatically translated. Korean, Chinese, "
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
                "order. Use arrows and Enter in autocomplete, and Escape to close it. "
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
                "or search-history database. Google Analytics measures visits and usage and may process page addresses, browser/device information and analytics cookies. Default page and referrer addresses omit search parameters; search terms and character inputs are not sent as custom events. Google signals and advertising personalization are disabled. Theme "
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
                "顶部语言设置决定结果的主要语言。关键词在四种语言中一起搜索，不会机器翻译。支持韩语、中文、日语、英语。用方向键和 Enter "
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
                "Tab 按关键词、说话角色、提及角色、搜索的顺序移动，Shift+Tab 反向移动。自动完成列表可用方向键和 Enter 选择、Esc "
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
                "角色名、词句、语言和先行剧情选项以 URL 参数发送至服务器，可能出现在托管日志或分享链接中。本应用不建立账号或搜索历史数据库，使用 Google Analytics 统计访问和使用情况，Google 可能处理页面地址、浏览器及设备信息和分析 Cookie。默认页面及来源地址不含搜索参数，不将搜索词和角色输入作为自定义事件发送，不启用 Google 信号和广告个性化。主题存于 "
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
                "上部の言語設定が結果の主言語になります。どの言語の語句でも四言語の原文から検索します。検索語の機械翻訳は行いません。韓国語・中国語・日本語・英語に対応します。方向キーと "
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
                "Tabは語句、話す人物、言及する人物、検索の順に移動し、Shift+Tabは逆順です。候補は方向キーとEnterで選択し、Escで閉じます。別の言語で人物名を入力しても、選んだ台詞言語の名前が候補に表示されます。",
            ),
            (
                "結果の順序と共通の文脈",
                "二人の検索では同じ分岐で相手の発言が近くにある一致を優先します。前後それぞれ原文60行以内のテキスト6行まで確認し、別の話者や分岐で止めます。直接の呼びかけや第三者への言及を確定するものではなく、名前が一致しない台詞は追加しません。同じファイル・分岐の近い一致は文脈を共有します。話者が明記されない字幕・地の文・選択肢に人物を推測して付けません。",
            ),
        ],
        "privacy": [
            (
                "リクエストと保存",
                "人物名・語句・言語・先行ストーリー設定はURLパラメータとしてサーバーに送信され、ホスティングのログや共有リンクに含まれる場合があります。アカウントや検索履歴DBは作成しません。Google Analyticsで訪問・利用状況を測定し、ページURL・ブラウザーや端末情報・分析CookieなどがGoogleで処理される場合があります。初期ページと参照URLから検索パラメーターを除き、検索語句や人物入力値を独自イベントでは送信しません。Googleシグナルと広告のパーソナライズは無効です。テーマはlocalStorage、更新の再通知はsessionStorageに保存します。アプリ独自のCookieは設定しません。",
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


COMPARISON_HELP = {
    "ko": ("다국어 검색과 함께 보기", "어느 언어의 단어나 문구든 입력하면 한국어·중국어·일본어·영어 대사에서 함께 찾습니다. 검증된 같은 대사는 하나로 묶고 페이지 언어의 대사를 가장 크게 표시합니다. 결과 위 언어 버튼을 켜고 끄면 다른 언어와 펼친 문맥에 즉시 적용됩니다. 페이지 언어는 항상 표시합니다. 대응을 확인하지 못하면 검색된 언어와 안내를 표시하며, 기계 번역이나 같은 물리 행 번호로 채우지 않습니다. 구조 검증은 의미상 정확성을 보증하지 않으므로 각 언어의 ?와 문맥을 확인하세요. 짧고 흔한 표현은 결과가 많아 검색 시간이 늘어날 수 있습니다."),
    "en": ("Multilingual search and display", "Search a word or phrase in any of the four languages. Verified counterparts are deduplicated and the page language is displayed most prominently. Toggle result language buttons to instantly show additional languages, including open context, without rerunning the search. The page language stays visible. If no verified counterpart exists, the matched language is shown with a notice. No machine translation or physical line-number guesses are used. Structural correspondence is not a semantic guarantee; inspect context and each language's details. Very common words may take longer."),
    "ja": ("多言語検索と併記", "四言語のどの語句でも検索できます。検証済みの同じ台詞はまとめ、ページ言語を最も大きく表示します。結果上部の言語ボタンで他言語と開いた文脈の表示を即座に切り替えます。ページ言語は常に表示します。対応未確認の場合は検索で見つかった言語と案内を表示します。機械翻訳や物理行番号による推測は行いません。構造上の対応は意味の一致を保証しません。文脈と各言語の詳細を確認してください。よく使われる短い語句は検索に時間がかかることがあります。"),
    "zh": ("多语言搜索与并列显示", "可输入任意一种语言的词句，在四种语言中一起搜索。已验证的同一台词合并显示，以页面语言为主要台词。结果上方的语言按钮可即时切换其他语言及已展开上下文，无需重新搜索。页面语言始终显示。对应未经确认时显示匹配语言及提示，不会机器翻译或按物理行号猜测。结构对应不保证语义一致，请结合上下文及各语言详情判断。常见短词可能需要更多搜索时间。"),
}
for lang, (title, text) in COMPARISON_HELP.items():
    if lang == "ko":
        PAGES["help"]["sections"].append({"title": title, "paragraphs": [text]})
    else:
        COPY[lang]["help"].append((title, text))

PAGES["changelog"]["sections"].insert(
    0,
    {
        "title": "1.1.0 · 2026-10-23",
        "paragraphs": [
            "중국어 원문과 한국어·일본어·영어 번역 대조 검색을 추가했습니다. 동일한 명령·분기 구조를 검증한 파일에서만 대응 대사를 표시하며, 앞뒤 문맥도 함께 대조할 수 있습니다."
        ],
    },
)
for lang, text in {
    "en": "Added comparison search for Chinese originals and Korean, Japanese or English translations, including context. Correspondences are limited to files with verified matching command and branch structure.",
    "ja": "中国語原文と韓国語・日本語・英語訳文の比較検索を追加しました。命令・分岐構造が一致するファイルのみ対応台詞を表示し、前後の文脈も比較できます。",
    "zh": "新增中文原文与韩语、日语、英语译文对照搜索，并支持上下文对照。仅显示经验证命令和分支结构一致的文件中的对应台词。",
}.items():
    COPY[lang]["changelog"].insert(0, ("1.1.0 · 2026-10-23", text))


PAGES["changelog"]["sections"].insert(0, {
    "title": "1.2.0 · 2026-10-23",
    "paragraphs": ["네 언어의 대사를 함께 검색하고 페이지 언어를 중심으로 표시합니다. 결과에서 다른 언어를 즉시 켜고 끌 수 있습니다. 최근 검색으로 돌아오면 추가로 불러온 결과와 펼친 문맥, 읽던 위치를 복원합니다."],
})
for lang, text in {
    "en": "Search all four languages together, with the page language displayed most prominently. Toggle additional languages immediately. Returning to recent searches restores loaded results, open context and reading position.",
    "ja": "四言語をまとめて検索し、ページ言語を中心に表示します。他言語の併記は即座に切り替えられます。最近の検索に戻ると、追加した結果・開いた文脈・読んでいた位置を復元します。",
    "zh": "四种语言一起搜索，以页面语言为主要显示，并可即时切换其他语言。返回最近的搜索时，恢复已加载的结果、展开的上下文和阅读位置。",
}.items():
    COPY[lang]["changelog"].insert(0, ("1.2.0 · 2026-10-23", text))


for lang, text in {
    "ko": "대사 검색어는 민트색으로, 찾을 인물의 실제 이름·등록 표기는 옅은 금색 밑줄로 표시합니다. 다른 언어와 문맥에도 해당 언어의 이름을 표시하며, 이름 일치가 직접 호칭이나 대화 상대를 뜻하지는 않습니다.",
    "en": "Searched phrases use mint highlights; literal names of the character mentioned use pale gold and an underline, including localized variants and context. A name match does not confirm an addressee or direct address.",
    "ja": "検索語句はミント色、検索対象の人物名・登録表記は薄い金色と下線で表示します。他言語と文脈にも適用します。名前の一致は呼びかけや会話相手を確定するものではありません。",
    "zh": "搜索词句以薄荷色标记，提及角色的实际姓名及登记表记以浅金色和下划线标记，同时适用于其他语言和上下文。姓名匹配不表示已确认称呼或对话对象。",
}.items():
    if lang == "ko":
        PAGES["help"]["sections"][-1]["paragraphs"].append(text)
    else:
        title, previous = COPY[lang]["help"][-1]
        COPY[lang]["help"][-1] = (title, previous + " " + text)


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
