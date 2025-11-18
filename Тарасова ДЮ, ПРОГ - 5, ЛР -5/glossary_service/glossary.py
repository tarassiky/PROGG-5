import json
import os


class Glossary:
    def __init__(self, data_file="glossary_data.json"):
        self.data_file = data_file
        self.terms = self._load_data()

    def _load_data(self):
        """Загружает данные глоссария из JSON файла"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Начальные данные глоссария Python
            initial_data = {
                "variable": {
                    "term": "variable",
                    "definition": "Именованная область памяти для хранения данных, которая может изменяться в ходе выполнения программы.",
                    "category": "basic",
                    "examples": "x = 5\nname = 'Alice'"
                },
                "function": {
                    "term": "function",
                    "definition": "Блок многократно используемого кода, который выполняет определенную задачу.",
                    "category": "basic",
                    "examples": "def greet(name):\n    return f'Hello, {name}!'"
                },
                "class": {
                    "term": "class",
                    "definition": "Шаблон для создания объектов, определяющий их свойства и поведение.",
                    "category": "OOP",
                    "examples": "class Dog:\n    def __init__(self, name):\n        self.name = name"
                },
                "list": {
                    "term": "list",
                    "definition": "Изменяемая упорядоченная коллекция элементов различных типов.",
                    "category": "data_structures",
                    "examples": "numbers = [1, 2, 3, 4, 5]"
                },
                "dictionary": {
                    "term": "dictionary",
                    "definition": "Неупорядоченная коллекция пар ключ-значение.",
                    "category": "data_structures",
                    "examples": "person = {'name': 'John', 'age': 30}"
                }
            }
            self._save_data(initial_data)
            return initial_data

    def _save_data(self, data):
        """Сохраняет данные в JSON файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_term(self, term):
        """Возвращает определение термина"""
        return self.terms.get(term.lower())

    def search_terms(self, query):
        """Ищет термины по запросу"""
        query = query.lower()
        results = []
        for term, data in self.terms.items():
            if (query in term.lower() or
                    query in data['definition'].lower() or
                    query in data.get('examples', '').lower()):
                results.append(data)
        return results

    def get_all_terms(self):
        """Возвращает все термины"""
        return list(self.terms.values())

    def add_term(self, term, definition, category="general", examples=""):
        """Добавляет новый термин в глоссарий"""
        term_key = term.lower()
        if term_key in self.terms:
            return False, "Термин уже существует"

        self.terms[term_key] = {
            "term": term,
            "definition": definition,
            "category": category,
            "examples": examples
        }
        self._save_data(self.terms)
        return True, "Термин успешно добавлен"