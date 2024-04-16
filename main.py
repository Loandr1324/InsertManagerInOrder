# Author Loik Andrey mail: loikand@mail.ru
# 1. Просмотр массива заказов и отбор заказов по условиям
# 2. условия отбора - отбирать заказы, соответствующе ВСЕМ условиями
# 2.1. поле «Клиент» НЕ содержит «Сотрудник»
# 2.2. поле «Менеджер» = «»
# 2.3. Дата создания заказа  - диапазон:
# начало диапазона = «дата запуска скрипта» - 1 день / конец диапазона = «дата запуска скрипта»
# [23.02.2024 20:13]
# Давай здесь изменим
# начало диапазона = «дата запуска скрипта» - 3 дня

# 3. Действия с отобранным заказом
# 3.1. Если поле «Заметка к заказу» ('notes’) содержит «Номер исходного заказа»,
# то установить поле «Менеджер» = значение поля «Автор заметки» и удалить заметку,
# содержащую текст «Номер исходного заказа»
# 3.2. Если поле «Заметка к заказу» ('notes’) НЕ содержит «Номер исходного заказа»,
# то установить поле «Менеджер» = сотрудник «0 Менеджер не определен» (ID: 25191325)
# 4. Частота запуска скрипта: 1 раз в час в интервале с 8:00 до 19:00

import datetime as dt
import asyncio
from aioabcpapi import Abcp
from config import AUTH_API, FILE_NAME_CONFIG, FRANCHISES
from loguru import logger

# Задаём параметры логирования
logger.add(FILE_NAME_CONFIG,
           format="{time:DD/MM/YY HH:mm:ss} - {file} - {level} - {message}",
           level="INFO",
           rotation="1 month",
           compression="zip")

host, login, password = AUTH_API['HOST_API'], AUTH_API['USER_API'], AUTH_API['PASSWORD_API']
api = Abcp(host, login, password)


async def get_list_orders(date_start: dt or str) -> list:
    """
    Получаем список заказов с даты размещения
    :param date_start: Начальная дата размещения заказа в формате ГГГГ-ММ-ДД ЧЧ:мм:СС
    :return:
    """
    return await api.cp.admin.orders.get_orders_list(date_created_start=date_start, format='short')


async def get_id_manager(note):
    """
    Выбираем id менеджера по автору заметки из списка менеджеров или устанавливаем заданное значение (id: 25191325)
    :param note: Первая заметка в заказе
    :return:
    """
    if 'Номер исходного заказа' in note['value']:
        # Получаем актуальный список менеджеров
        list_managers = await api.cp.admin.staff.get()

        # Находим менеджера по имени автора заметки в списке менеджеров по значению ключа lastName
        author_notes = note['author'].split(" ", 1)
        manager = list(
            filter(lambda v: v["firstName"] == author_notes[0] and v["lastName"] == author_notes[1], list_managers)
        )[0]
        id_manager = manager['id']
    else:
        id_manager = '25191325'
    return id_manager


async def main():
    """
    Весь рабочий процесс программы по подстановке менеджера в заказы без менеджера.
    1. Получаем список заказов начиная с указанной даты.
    2. Находим заказы, в которых необходимо проставить менеджера.
    3. Устанавливаем менеджера согласно задания и удаляем первый комментарий.
    """
    logger.info(f"... Запуск программы")
    # 1. Получаем список заказов начиная с указанной в ТЗ даты
    time_start = (dt.datetime.now() - dt.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    list_orders = await get_list_orders(time_start)

    # 2. Фильтруем согласно ТЗ полученный список заказов
    filter_orders = list(
        filter(lambda v: v['managerId'] == '0' and 'Сотрудник' not in v['userName'] and v['userCode'] not in FRANCHISES,
               list_orders)
    )

    # 2.1. Доработка 15.04.2024г. Фильтруем заказы по списку франчайзи FRANCHISES с неустановленным менеджером
    filter_orders_franch = list(filter(lambda v: v['managerId'] == '0' and v['userCode'] in FRANCHISES, list_orders))

    # Дальнейшую работу выполняем, если отфильтрованный список не пустой.
    # 3. Устанавливаем менеджера
    if filter_orders:
        for i in filter_orders:
            logger.info(f"Получили заказ для внесения изменений {i['managerId']=} и {i['userName']}")
            logger.info(f"Все данные по заказу {i}")
            # Получаем необходимые данные для изменения заказа
            id_manager = await get_id_manager(i['notes'][0])
            # Убираем первую заметку
            id_note = i['notes'][0]['id']
            number = i['number']

            logger.info(f"Начинаем вносить изменения с параметрами {number=}, {id_manager=}, {id_note=}")
            # Изменяем данные в заказе на платформе abcp
            result = await api.cp.admin.orders.create_or_edit_order(
                number=number, manager_id=id_manager, del_note=id_note
            )
            logger.info(f"Результат внесения изменения в заказ {result=}")

    # 3.1. Доработка 15.04.2024г. подстановка менеджера в заказы франчайзи
    if filter_orders_franch:
        for order in filter_orders_franch:
            logger.info(f"Получили заказ франчайзи для внесения изменений {order['managerId']=} и {order['userName']=}")
            logger.info(f"Все данные по заказу {order}")
            id_manager = FRANCHISES[order['userCode']]
            number = order['number']
            # Изменяем данные в заказе на платформе abcp
            result = await api.cp.admin.orders.create_or_edit_order(
                number=number, manager_id=id_manager
            )
            logger.info(f"Результат внесения изменения в заказ франчайзи {result=}")

    logger.info(f"... Программа завершена")
    await api._base.close()  # В будущих релизах библиотеки планируется автоматически закрывать сессию


if __name__ == '__main__':
    asyncio.run(main())
