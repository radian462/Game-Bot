import csv
import os

from Modules.logger import make_logger

logger = make_logger("Translator")


class Translator:
    def __init__(self, lang: str = "ja"):
        self.lang = lang
        self.file_path = "Resources/Translate.csv"
        self.translations: dict[str, str] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            logger.warning(f"Translation file not found: {self.file_path}")
            return

        with open(self.file_path, mode="r", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile)

            header_found = False

            for row in reader:
                if not row or row[0].startswith("#"):
                    continue

                if not header_found:
                    langs = row[1:]
                    self.translations = {lang: {} for lang in langs}
                    header_found = True
                else:
                    for i, text in enumerate(row):
                        if i != 0:
                            lang = langs[i - 1]
                            self.translations[lang][row[0]] = text

            logger.info(f"Loaded translations data from {self.file_path}")

    def change_lang(self, lang: str):
        self.lang = lang
        logger.info(f"Changed language to {lang}")

    def getstring(self, text: str, lang: str | None = None) -> str:
        lang = lang or self.lang
        return self.translations.get(lang, {}).get(text, text)


if __name__ == "__main__":
    t = Translator()

    print(t.getstring("Fox"))  # デフォルト言語 (ja) の翻訳を表示
    print(t.getstring("TeruTeru"))  # デフォルト言語 (ja) の翻訳を表示
    print(t.getstring("Fox", "en"))
