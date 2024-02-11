import logging
import pytest
from playwright.sync_api import sync_playwright, expect

TODO_MVC_URL = "https://todomvc.com/examples/emberjs/todomvc/dist/"

@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()

@pytest.fixture(scope='module')
def page(browser):
    page = browser.new_page()
    page.goto(TODO_MVC_URL)
    yield page

def test_page_loaded_correctly(page):
    assert page.is_visible("body")
    assert page.inner_text(".header h1") == "todos"
    assert page.locator("input.new-todo").is_visible()
    assert page.locator("input.new-todo").get_attribute("placeholder") == "What needs to be done?"

def test_check_tasks_existence(page):
    tasks = page.locator(".todo-list li")
    tasks_count = tasks.count()

    if tasks_count == 0:
        assert not tasks.is_visible()
        logging.info("На сторінці немає завдань.")
    else:
        assert tasks.is_visible()
        logging.info(f"Кількість поточних завдань: {tasks_count}")

@pytest.mark.parametrize("new_task_name", ["TaskCreateNewTaskCheck"])
def test_create_and_check_task(page, new_task_name):
    tasks = page.locator(".todo-list li")
    tasks_count = tasks.count()

    page.type(".new-todo", new_task_name)
    page.keyboard.press("Enter")

    tasks_count_after = tasks.count()
    assert tasks_count_after == tasks_count + 1

    new_task = page.locator(f".todo-list li:has-text('{new_task_name}')")
    assert new_task.is_visible()
    logging.info(f"\nКількість поточних завдань: {tasks_count_after}")

def test_delete_task_by_name(page):
    tasks = page.locator(".todo-list li")
    tasks_count = tasks.count()

    if tasks_count > 0:
        task_to_delete_name = "TaskCreateNewTaskCheck"
        try:
            page.locator(f"[data-testid='todo-title']:has-text('{task_to_delete_name}')"
                         "button[aria-label='Delete'].destroy").click()
            page.wait_for_selector(f".todo-list li:has-text('{task_to_delete_name}')", state='hidden')

            tasks_count_after_delete = tasks.count()
            assert tasks_count_after_delete == tasks_count - 1
            logging.info(f"\nКількість поточних завдань після видалення: {tasks_count_after_delete}")
        except Exception as e:
            logging.error(f"\nПомилка при видаленні завдання: {e}")
    else:
        logging.info("\nНа сторінці немає завдань для видалення.")

def test_create_task_and_check_status(page):
    page.goto("https://demo.playwright.dev/todomvc/#/")
    page.get_by_placeholder("What needs to be done?").click()
    page.get_by_placeholder("What needs to be done?").fill("apple")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.get_by_placeholder("What needs to be done?").fill("banana and strawberry")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.locator("li").filter(has_text="apple").get_by_label("Toggle Todo").check()
    page.get_by_role("link", name="Completed").click()
    page.get_by_role("link", name="Active").click()
    expect(page.get_by_test_id("todo-title")).to_contain_text("banana and strawberry")
    page.get_by_role("link", name="All").click()
    tasks_count = page.locator("[data-testid='todo-title']").count()
    assert tasks_count == 2

def test_reload_page_and_check_task_existence(page):
    page.reload()
    reloaded_tasks_count = page.locator("[data-testid='todo-title']").count()
    assert reloaded_tasks_count == 2

def test_delete_all_tasks(page):
    while True:
        if page.locator(".destroy").count() > 0:
            page.locator("[data-testid='todo-title']").nth(-1).hover()
            page.locator(".destroy").nth(-1).click()
        else:
            break
    assert page.locator("[data-testid='todo-title']").count() == 0

def test_toggle_task_completion(page):
    # Створення нового завдання
    new_task_name = "TaskToToggle"
    page.type(".new-todo", new_task_name)
    page.keyboard.press("Enter")

    # Отримання новоствореного завдання
    new_task = page.locator(f".todo-list li:has-text('{new_task_name}')")

    # Перевірка, що завдання не відмічене як виконане
    assert "completed" not in new_task.get_attribute("class")

    # Відмітка завдання як виконане
    new_task.get_by_label("Toggle Todo").check()

    # Перевірка, що завдання відмічене як виконане
    assert "completed" in new_task.get_attribute("class")

def test_delete_all_tasks(page):
    # Перевірка, що на сторінці є завдання для видалення
    assert page.locator(".todo-list li").count() > 0

    # Видалення всіх завдань
    while page.locator(".destroy").count() > 0:
        # Наведення курсора на останнє завдання у списку
        page.locator("[data-testid='todo-title']").nth(-1).hover()

        # Клік на кнопку видалення
        page.locator(".destroy").nth(-1).click()

    # Перевірка, що всі завдання були видалені
    assert page.locator("[data-testid='todo-title']").count() == 0

def test_display_active_tasks(page):
    # Створення кількох завдань, деякі з яких виконані
    page.type(".new-todo", "Task 1")
    page.keyboard.press("Enter")
    page.type(".new-todo", "Task 2")
    page.keyboard.press("Enter")
    page.type(".new-todo", "Task 3")
    page.keyboard.press("Enter")
    page.locator(".todo-list li").nth(1).get_by_label("Toggle Todo").check()

    # Клік на посилання "Active"
    page.get_by_role("link", name="Active").click()

    # Перевірка, що на сторінці відображаються тільки активні завдання
    assert page.locator("[data-testid='todo-title']").count() == 2

def test_edit_task_by_enter(page):
    # Створюємо нове завдання
    new_task_name = "Task to Edit"
    page.type(".new-todo", new_task_name)
    page.keyboard.press("Enter")

    # Редагуємо завдання, натискаючи клавішу "Enter"
    edited_task_name = "Edited Task"
    page.dblclick(f".todo-list li:has-text('{new_task_name}')")
    page.type(f".todo-list li:has-text('{new_task_name}') input.edit", edited_task_name)
    page.keyboard.press("Enter")

    # Перевіряємо, що завдання було відредаговано правильно
    edited_task = page.locator(f".todo-list li:has-text('{edited_task_name}')")
    assert edited_task.is_visible()

def test_edit_task_by_tab(page):
    # Створюємо нове завдання
    new_task_name = "Task to Edit by Tab"
    page.type(".new-todo", new_task_name)
    page.keyboard.press("Enter")

    # Редагуємо завдання, натискаючи клавішу "Tab"
    edited_task_name = "Edited Task by Tab"
    page.dblclick(f".todo-list li:has-text('{new_task_name}')")
    page.type(f".todo-list li:has-text('{new_task_name}') input.edit", edited_task_name)
    page.keyboard.press("Tab")

    # Перевіряємо, що завдання було відредаговано правильно
    edited_task = page.locator(f".todo-list li:has-text('{edited_task_name}')")
    assert edited_task.is_visible()

def test_edit_task_by_click_outside(page):
    # Створюємо нове завдання
    new_task_name = "Task to Edit by Click Outside"
    page.type(".new-todo", new_task_name)
    page.keyboard.press("Enter")

    # Редагуємо завдання, натискаючи поза ним
    edited_task_name = "Edited Task by Click Outside"
    page.dblclick(f".todo-list li:has-text('{new_task_name}')")
    page.type(f".todo-list li:has-text('{new_task_name}') input.edit", edited_task_name)
    page.click("body")

    # Перевіряємо, що завдання було відредаговано правильно
    edited_task = page.locator(f".todo-list li:has-text('{edited_task_name}')")
    assert edited_task.is_visible()

def test_cancel_edit_by_esc(page):
    # Створюємо нове завдання
    new_task_name = "Task to Cancel Edit by Esc"
    page.type(".new-todo", new_task_name)
    page.keyboard.press("Enter")

    # Редагуємо завдання та відміняємо редагування натисканням "Esc"
    edited_task_name = "Edited Task by Esc"
    page.dblclick(f".todo-list li:has-text('{new_task_name}')")
    page.type(f".todo-list li:has-text('{new_task_name}') input.edit", edited_task_name)
    page.keyboard.press("Escape")

    # Перевіряємо, що завдання залишається незмінним
    original_task = page.locator(f".todo-list li:has-text('{new_task_name}')")
    assert original_task.is_visible()

@pytest.mark.xfail(reason="This test is expected to fail due to a known issue.")
def test_unknown_test():
    raise ValueError("Unknown test encountered.")

if __name__ == "__main__":
    pytest.main(["-v"])

