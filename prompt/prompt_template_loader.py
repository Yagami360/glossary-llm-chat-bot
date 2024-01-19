import yaml
from langchain import PromptTemplate


class PromptTemplateLoader():
    def __init__(self, file_path):
        with open(file_path, 'r') as yml:
            prompt_yml = yaml.safe_load(yml)

        self.input_variables = prompt_yml["inputVariables"]
        self.template = prompt_yml["promptTemplate"]
        self.prompt_template = PromptTemplate(template=self.template, input_variables=self.input_variables)
        return

    def format(self, **kwargs):
        prompt = self.prompt_template.format(**kwargs)
        return prompt


if __name__ == "__main__":
    try:
        prompt_template = PromptTemplateLoader(file_path='prompt_files/prompt_2.yml')
        prompt = prompt_template.format(question="hogehogeについて教えて", context="hogehogeとは、プログラムのサンプルコードなどで、特に意味がない何を入れてもかまわないときに使う言葉")
        print("prompt: ", prompt)
    except Exception as e:
        print(f"Exception was occurred! | {e}")
