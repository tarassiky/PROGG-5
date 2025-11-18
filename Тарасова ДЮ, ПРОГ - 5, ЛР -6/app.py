import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import datetime
import asyncio
import aiohttp
import os
from typing import Dict, Set, Any, Optional

# Конфигурация
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CURRENCIES = ['USD', 'EUR', 'GBP', 'CNY', 'JPY']


class CurrencyObserver:
    """Subject (Наблюдаемый объект) для паттерна Наблюдатель"""

    def __init__(self) -> None:
        self._observers: Set['CurrencyWebSocket'] = set()
        self._rates: Dict[str, float] = {currency: 0.0 for currency in CURRENCIES}

    def register(self, observer: 'CurrencyWebSocket') -> None:
        """Регистрация наблюдателя"""
        self._observers.add(observer)
        print(f"👥 Наблюдатель зарегистрирован. Всего: {len(self._observers)}")

    def unregister(self, observer: 'CurrencyWebSocket') -> None:
        """Удаление наблюдателя"""
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"👥 Наблюдатель удален. Всего: {len(self._observers)}")

    def update_rates(self, new_rates: Dict[str, float]) -> None:
        """Обновление курсов и уведомление наблюдателей"""
        changes = self._calculate_changes(new_rates)
        self._rates.update(new_rates)

        # Всегда уведомляем наблюдателей о текущих курсах
        self.notify_observers(changes)

    def _calculate_changes(self, new_rates: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """Вычисление изменений курсов"""
        changes = {}
        for currency, new_rate in new_rates.items():
            old_rate = self._rates.get(currency, 0)
            if old_rate and old_rate != new_rate:
                changes[currency] = {
                    'previous': round(old_rate, 4),
                    'current': round(new_rate, 4),
                    'change': round(new_rate - old_rate, 4),
                    'change_percent': round(((new_rate - old_rate) / old_rate) * 100, 2)
                }
        return changes

    def notify_observers(self, changes: Dict[str, Dict[str, Any]]) -> None:
        """Уведомление всех наблюдателей"""
        data = {
            'type': 'currency_rates',
            'rates': self._rates,
            'changes': changes,
            'timestamp': datetime.datetime.now().isoformat(),
            'observer_count': len(self._observers)
        }

        for observer in self._observers.copy():
            try:
                observer.send_update(data)
            except Exception as e:
                print(f"❌ Ошибка отправки наблюдателю: {e}")
                self.unregister(observer)


class CurrencyWebSocket(tornado.websocket.WebSocketHandler):
    """WebSocket handler для клиентов-наблюдателей"""

    def initialize(self, observer: CurrencyObserver) -> None:
        self.observer = observer
        self.client_id: int = id(self)

    def open(self) -> None:
        """При подключении клиента"""
        print(f"🔌 WebSocket подключен: {self.client_id}")
        self.observer.register(self)

        # Отправляем приветственное сообщение
        self.send_message({
            'type': 'connection',
            'client_id': self.client_id,
            'message': 'Подключено к серверу курсов валют'
        })

        # Отправляем текущие курсы
        self.send_current_rates()

    def send_current_rates(self) -> None:
        """Отправка текущих курсов клиенту"""
        data = {
            'type': 'currency_rates',
            'rates': self.observer._rates,
            'changes': {},
            'timestamp': datetime.datetime.now().isoformat(),
            'observer_count': len(self.observer._observers)
        }
        self.send_message(data)

    def on_message(self, message: str) -> None:
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            if data.get('type') == 'ping':
                self.send_message({'type': 'pong'})
            elif data.get('type') == 'refresh':
                self.send_current_rates()
        except json.JSONDecodeError:
            pass

    def on_close(self) -> None:
        """При закрытии соединения"""
        print(f"🔌 WebSocket отключен: {self.client_id}")
        self.observer.unregister(self)

    def send_message(self, data: Dict[str, Any]) -> None:
        """Отправка сообщения клиенту"""
        try:
            self.write_message(json.dumps(data))
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")

    def send_update(self, data: Dict[str, Any]) -> None:
        """Отправка обновления курсов (вызывается наблюдателем)"""
        self.send_message(data)

    def check_origin(self, origin: str) -> bool:
        return True


class MainHandler(tornado.web.RequestHandler):
    """Главная страница"""

    def get(self) -> None:
        self.render("index.html")


async def fetch_currency_rates() -> Optional[Dict[str, float]]:
    """Получение курсов валют с API ЦБ РФ"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CBR_API_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = {}

                    for currency in CURRENCIES:
                        if currency in data.get('Valute', {}):
                            rates[currency] = data['Valute'][currency]['Value']

                    print(f"✅ Получены курсы с API: {rates}")
                    return rates
                else:
                    print(f"❌ Ошибка API: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Ошибка запроса к API: {e}")
        return None


async def monitor_currencies(observer: CurrencyObserver) -> None:
    """Фоновая задача для мониторинга изменений курсов"""
    # Сначала получаем начальные курсы
    print("🔄 Первоначальная загрузка курсов...")
    initial_rates = await fetch_currency_rates()

    if initial_rates:
        observer.update_rates(initial_rates)
    else:
        # Тестовые данные если API недоступно
        test_rates = {
            'USD': 75.50,
            'EUR': 80.25,
            'GBP': 95.75,
            'CNY': 10.45,
            'JPY': 0.65
        }
        observer.update_rates(test_rates)

    # Затем запускаем периодическую проверку
    counter = 0
    while True:
        try:
            counter += 1
            print(f"🔄 Проверка обновлений курсов #{counter}...")
            new_rates = await fetch_currency_rates()

            if new_rates:
                observer.update_rates(new_rates)
            else:
                # Тестовые данные с небольшими изменениями если API недоступно
                current_rates = observer._rates.copy()
                test_rates = {}
                for currency, rate in current_rates.items():
                    # Добавляем небольшие случайные изменения
                    change = (counter % 10) * 0.01
                    test_rates[currency] = rate + change

                print(f"📊 Используем тестовые данные: {test_rates}")
                observer.update_rates(test_rates)

            # Ждем 1 минуту до следующей проверки (для тестирования)
            await asyncio.sleep(60)

        except Exception as e:
            print(f"💥 Ошибка в мониторинге: {e}")
            await asyncio.sleep(30)


def make_app(observer: CurrencyObserver) -> tornado.web.Application:
    """Создание Tornado приложения"""
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", CurrencyWebSocket, {"observer": observer}),
    ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"))


async def main():
    """Основная функция запуска"""
    # Создаем observer до создания приложения
    observer = CurrencyObserver()
    app = make_app(observer)
    app.listen(8888)
    print("🚀 Сервер запущен на http://localhost:8888")

    # Запускаем мониторинг курсов в фоне
    asyncio.create_task(monitor_currencies(observer))

    print("✅ Мониторинг курсов запущен. Проверка каждые 60 секунд.")

    # Бесконечный цикл
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")