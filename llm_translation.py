from langchain_core.language_models import BaseChatModel


def translate_to_english(text: str, llm: BaseChatModel) -> str:
    return llm.invoke(
        "Translate the following text to English without adding any notes:\n\n" + text
    ).content


def translate_to_persian(text: str, llm: BaseChatModel) -> str:
    return llm.invoke(
        "Translate the following text to Persian without adding any notes.\n" +
        "Do not convert dates to Jalali calander and keep times in GMT.\n" +
        "Do not say anything before or after the translated text.\n" +
        "Here is the text to translate:\n\n" +
        text
    ).content




def replace_fa_numbers_with_en(text):
    fa_numbers = "۰۱۲۳۴۵۶۷۸۹"
    en_numbers = "0123456789"

    result = ""
    i = 0
    while i < len(text):
        if text[i] in fa_numbers:
            # Find the complete Persian number
            persian_num = ""
            while i < len(text) and text[i] in fa_numbers:
                persian_num += text[i]
                i += 1

            # Convert the Persian number to English format and append to result
            en_num = "".join([en_numbers[fa_numbers.index(char)] for char in persian_num])
            result += en_num
        else:
            result += text[i]
            i += 1

    return result

