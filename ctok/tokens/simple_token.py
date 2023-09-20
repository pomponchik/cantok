from ctok.tokens.abstract_token import AbstractToken


class SimpleToken(AbstractToken):
    def superpower(self) -> bool:
        return False

    def text_representation_of_superpower(self) -> str:
        return ''
