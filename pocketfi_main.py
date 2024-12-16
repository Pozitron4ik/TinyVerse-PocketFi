import requests
import os
import time
import logging
import json
import random
from forall import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

debug = True


class BrowserManager:

    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.driver = None

    def check_browser_status(self):
        try:
            response = requests.get(
                'http://local.adspower.net:50325/api/v1/browser/active',
                params={'serial_number': self.serial_number}
            )
            data = response.json()
            if data['code'] == 0 and data['data']['status'] == 'Active':
                logging.info(f"Account {self.serial_number}: Browser is already active.")
                return True
            else:
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in checking browser status: {str(e)}")
            return False

    def start_browser(self):
        try:
            if self.check_browser_status():
                logging.info(f"Account {self.serial_number}: Browser already open. Closing the existing browser.")
                self.close_browser()
                time.sleep(5)

            script_dir = os.path.dirname(os.path.abspath(__file__))
            requestly_extension_path = os.path.join(script_dir, 'blum_unlocker_extension')

            if debug:
                launch_args = json.dumps([f"--load-extension={requestly_extension_path}"])
                headless_param = "0"
            else:
                launch_args = json.dumps(["--headless=new", f"--load-extension={requestly_extension_path}"])
                headless_param = "1"

            request_url = (
                f'http://local.adspower.net:50325/api/v1/browser/start?'
                f'serial_number={self.serial_number}&ip_tab=1&headless={headless_param}&launch_args={launch_args}'
            )

            response = requests.get(request_url)
            data = response.json()
            if data['code'] == 0:
                selenium_address = data['data']['ws']['selenium']
                webdriver_path = data['data']['webdriver']
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", selenium_address)

                service = Service(executable_path=webdriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_window_size(600, 900)
                logging.info(f"Account {self.serial_number}: Browser started successfully.")
                return True
            else:
                logging.warning(f"Account {self.serial_number}: Failed to start the browser. Error: {data['msg']}")
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in starting browser: {str(e)}")
            return False

    def close_browser(self):
        try:
            if self.driver:
                try:
                    self.driver.close()
                    self.driver.quit()
                    self.driver = None
                    logging.info(f"Account {self.serial_number}: Browser closed successfully.")
                except WebDriverException as e:
                    logging.info(f"Account {self.serial_number}: exception, Browser should be closed now")
        except Exception as e:
            logging.exception(
                f"Account {self.serial_number}: General Exception occurred when trying to close the browser: {str(e)}")
        finally:
            try:
                response = requests.get(
                    'http://local.adspower.net:50325/api/v1/browser/stop',
                    params={'serial_number': self.serial_number}
                )
                data = response.json()
                if data['code'] == 0:
                    logging.info(f"Account {self.serial_number}: Browser closed successfully.")
                else:
                    logging.info(f"Account {self.serial_number}: exception, Browser should be closed now")
            except Exception as e:
                logging.exception(
                    f"Account {self.serial_number}: Exception occurred when trying to close the browser: {str(e)}")


class TelegramBotAutomation:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.browser_manager = BrowserManager(serial_number)
        logging.info(f"Initializing automation for account {serial_number}")
        self.browser_manager.start_browser()
        self.driver = self.browser_manager.driver

    def sleep(self, a, b):
        sleep_time = random.randrange(a, b)
        logging.info(f"Account {self.serial_number}: {sleep_time}sec sleep...")
        time.sleep(sleep_time)

    def navigate_to_bot(self):
        try:
            self.driver.get('https://web.telegram.org/k/')
            logging.info(f"Account {self.serial_number}: Navigated to Telegram web.")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in navigating to Telegram bot: {str(e)}")
            self.browser_manager.close_browser()

    def send_message(self, message):
        chat_input_area = self.wait_for_element(By.XPATH,
                                                '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]')
        chat_input_area.click()
        chat_input_area.send_keys(message)

        search_area = self.wait_for_element(By.XPATH,
                                            '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]')
        search_area.click()
        logging.info(f"Account {self.serial_number}: Group searched.")
        self.sleep(2, 3)

    def click_link(self):
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='t.me/pocketfi_bot/mining']")
        link.click()

        # После последней обновы 31.08.24 закомментил
        # launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
        # launch_click.click()
        logging.info(f"Account {self.serial_number}: POCKET STARTED")
        sleep_time = random.randrange(3, 5)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return

    def click_launch_button(self):
        try:
            logging.info(f"Account {self.serial_number}: trying to click launch button first time")
            launch_button = self.wait_for_element(By.XPATH,
                                                  "/html[1]/body[1]/div[6]/div[1]/div[2]/button[1]/div[1]",
                                                  timeout=5)
            if launch_button:
                self.driver.execute_script("arguments[0].click();", launch_button)
                self.switch_to_iframe()
                time.sleep(3)
            else:
                logging.info(f"Account {self.serial_number}: Launch button not found (first time).")
        except TimeoutException:
            logging.info(f"Account {self.serial_number}: Launch button not found due to timeout (first time).")

        except WebDriverException as e:
            logging.exception(
                f"Account {self.serial_number}: Exception occurred while clicking launch button: {str(e)}")

    def click_close_button(self):
        for attempt in range(2):
            try:
                button = self.wait_for_element(
                    By.XPATH,
                    "/html/body/div[1]/div/button"
                )
                button.click()
                self.sleep(2, 3)
                logging.info(f"Account {self.serial_number}: Clicked close button (attempt {attempt + 1}).")
            except TimeoutException:
                logging.info(
                    f"Account {self.serial_number}: Close button not found due to timeout (attempt {attempt + 1}).")
            except NoSuchElementException:
                logging.info(f"Account {self.serial_number}: Close button not found (attempt {attempt + 1}).")
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error in click_close_button (attempt {attempt + 1}): {e}")

    def click_what_simple_action_button(self):
        # Список текстов, по которым нужно кликнуть поочерёдно
        texts_in_order = ["What simple actions?", "What else is here?", "Calculate my mining speed"]

        for expected_text in texts_in_order:
            try:
                # Ищем кнопку каждый раз заново, предположим, что страница обновляет её текст
                button = self.wait_for_element(
                    By.XPATH,
                    "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/button[1]"
                )
                button_text = button.text.strip()

                if button_text == expected_text:
                    button.click()
                    logging.info(f"Account {self.serial_number}: Clicked button with text '{button_text}'.")
                    self.sleep(4, 6)
                else:
                    logging.info(
                        f"Account {self.serial_number}: Button text '{button_text}' does not match '{expected_text}', skipping click."
                    )
            except TimeoutException:
                logging.info(f"Account {self.serial_number}: button not found due to timeout.")
            except NoSuchElementException:
                logging.info(f"Account {self.serial_number}: button not found.")
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error while trying to click '{expected_text}': {e}")

    def click_start_mining_button(self):
        try:
            start_mining_button = self.wait_for_element(
                By.XPATH,
                "/html/body/div[6]/div/div[2]/div/div[2]/button"
            )
            start_mining_button.click()
            logging.info(f"Account {self.serial_number}: Clicked 'START MINING' button (no text check).")
            self.sleep(2, 3)

        except TimeoutException:
            logging.info(f"Account {self.serial_number}: 'START MINING' button not found due to timeout.")
        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: 'START MINING' button not found.")
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error in click_start_mining_button: {e}")



    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def switch_tabs(self):
        try:
            logging.info("Начинаем переключение вкладок.")

            tabs = self.driver.window_handles
            logging.info(f"Открыто {len(tabs)} вкладок.")

            current_tab = self.driver.current_window_handle
            current_index = tabs.index(current_tab)

            next_index = (current_index + 1) % len(tabs)
            logging.info(f"Переключаемся с вкладки {current_index} на {next_index}.")

            self.driver.switch_to.window(tabs[next_index])

            time.sleep(1)

            self.sleep(3, 7)

            logging.info("Переключаемся обратно на исходную вкладку.")
            self.driver.switch_to.window(tabs[current_index])

            logging.info("Переключаемся на iframe.")
            self.switch_to_iframe()

        except Exception as e:
            logging.error(f"Ошибка в аккаунте {self.serial_number}: {e}")

    def back(self):
        self.driver.switch_to.default_content()
        self.wait_for_element(By.XPATH,
                              '/html/body/div[6]/div/div[1]/button[1]'
                              ).click()
        time.sleep(2)

    def wait_for_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )

    def reboot(self):
        logging.info(f"Account {self.serial_number}: rebooting...")
        try:
            self.driver.switch_to.default_content()
            menu = self.wait_for_element(By.XPATH,
                                         '/html/body/div[6]/div/div[1]/div[1]/div/div[2]/button[1]/span[1]'
                                         )
            menu.click()
            self.driver.switch_to.default_content()
            time.sleep(4)
            reload = self.wait_for_element(By.XPATH,
                                           # #page-chats > div.btn-menu.contextmenu.bottom-center.active.was-open > div:nth-child(2)
                                           '/html/body/div[1]/div[3]/div[2]'
                                           )
            reload.click()
            self.sleep(2, 3)
            self.switch_to_iframe()
        except Exception as e:
            logging.info(f"Account {self.serial_number}: error rebooting")

    def daily(self):
        stage = 0
        # Шаг 1: Нажатие на "tasks"
        try:
            tasks = self.wait_for_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/button[2]')
            tasks.click()
            self.sleep(1, 4)
            logging.info(f"Account {self.serial_number}: clicked tasks")
            stage += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error clicking tasks: {e}, stage={stage}")

        # Шаг 2: Нажатие на "pocketfi"
        if stage > 0:
            try:
                pocketfi = self.wait_for_element(By.XPATH, '/html/body/div[1]/div/div[1]/div/div/div[2]/div/div[3]')
                pocketfi.click()
                self.sleep(1, 4)
                logging.info(f"Account {self.serial_number}: clicked pocketfi")
                stage += 1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error clicking pocketfi: {e}, stage={stage}")

        # Шаг 3: Нажатие на "daily boost"
        if stage > 1:
            try:
                boost = self.wait_for_element(
                    By.CSS_SELECTOR,
                    '#app > div > div.bg-new-background-primary.h-screen.w-screen.fixed.top-0.left-0.overflow-y-auto'
                    '.overflow-x-hidden.undefined > div > div > div.flex.flex-col.gap-3.w-full > '
                    'div:nth-child(1) > div:nth-child(2)'
                )
                boost.click()
                self.sleep(3, 5)
                logging.info(f"Account {self.serial_number}: clicked daily boost")
                stage += 1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error clicking daily boost: {e}, stage={stage}")

        # Шаг 4: Claim daily reward
        if stage > 2:
            try:
                self.driver.switch_to.default_content()

                reward_button = self.wait_for_element(By.XPATH,
                                                      "//button[contains(text(),'reward') or contains(text(),'Come')]")
                button_text = reward_button.text.strip()

                button_text_upper = button_text.upper()

                if button_text_upper == "CLAIM DAILY REWARD":
                    self.driver.execute_script("arguments[0].click();", reward_button)
                    self.sleep(1, 4)
                    logging.info(f"Account {self.serial_number}: clicked 'claim daily reward'")
                    stage += 1
                elif button_text_upper == "COME BACK TOMORROW":
                    logging.info(f"Account {self.serial_number}: 'Come back tomorrow', skipping click.")
                    stage += 1
                else:
                    logging.info(
                        f"Account {self.serial_number}: Unexpected button text '{button_text}', skipping click.")
                    stage += 1

            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error handling daily reward button: {e}, stage={stage}")

        if stage > 3:
            try:
                self.reboot()
                stage += 1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error rebooting, stage={stage}")

        # Шаг 6: Switch to mining
        if stage > 4:
            try:
                switch_to_mining = self.wait_for_element(
                    By.CSS_SELECTOR,
                    '#app > div > div.fixed.bottom-0.left-0.w-screen > div > button:nth-child(1)'
                )
                switch_to_mining.click()
                self.sleep(2, 3)
                logging.info(f"Account {self.serial_number}: switched to mining")
                stage += 1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error switching to mining: {e}, stage={stage}")

    def claim(self):
        try:
            # Считываем первый номер
            try:
                first_num_element = self.wait_for_element(
                    By.XPATH,
                    "/html/body/div[1]/div/div[1]/div/div/div[3]/div[1]/div/span[2]"
                )
                first_num_text = first_num_element.text.strip()
                logging.info(f"Account {self.serial_number}: first_num_text='{first_num_text}'")
                first_num = float(first_num_text)
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error getting/converting first_num: {e}")
                return

            # Считываем второй номер
            try:
                second_num_element = self.wait_for_element(
                    By.XPATH,
                    "/html/body/div[1]/div/div[1]/div/div/div[3]/div[2]/span"
                )
                full_text = second_num_element.text.strip()
                logging.info(f"Account {self.serial_number}: second_full_text='{full_text}'")


                parts = full_text.split()
                second_num_text = parts[-1]
                logging.info(f"Account {self.serial_number}: extracted second_num_text='{second_num_text}'")

                second_num = float(second_num_text)
            except Exception as e:
                logging.info(f"Account {self.serial_number}: Error getting/converting second_num: {e}")
                return

            logging.info(f"Account {self.serial_number}: first_num={first_num}, second_num={second_num}")

            # Сравниваем числа
            if first_num >= second_num:
                try:
                    # Кликаем по кнопке claim
                    claimBut = self.wait_for_element(
                        By.CSS_SELECTOR,
                        '#app > div > div.bg-new-background-primary.h-screen.w-screen.fixed.top-0.left-0.overflow-y-auto'
                        '.overflow-x-hidden.\!bg-\[\#D9E1F1\] > div > div > '
                        'div.bg-white.shadow.rounded-20.p-5.py-7\.5.tall\:\!py-4.w-full.flex.items-center.'
                        'flex-col.justify-center.gap-5.tall\:gap-3.h-full.relative > '
                        'div.relative.mx-auto.h-\[260px\].tall\:h-\[220px\].flex.items-center.justify-center > div'
                    )
                    claimBut.click()
                    self.sleep(2, 3)
                    logging.info(f"Account {self.serial_number}: claimed")
                except Exception as e:
                    logging.info(f"Account {self.serial_number}: Error clicking claim button: {e}")
            else:
                # Если второй номер меньше первого, пропускаем клик
                logging.info(f"Account {self.serial_number}: second_num < first_num, skipping claim.")

        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error in claim: {str(e)}")


def read_accounts_from_file():
    with open('accounts_pocketfi.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


def write_accounts_to_file(accounts):
    with open('accounts_pocketfi.txt', 'w') as file:
        for account in accounts:
            file.write(f"{account}\n")


def process_accounts():
    last_processed_account = None

    while True:

        accounts = read_accounts_from_file()
        random.shuffle(accounts)
        write_accounts_to_file(accounts)
        i = 0
        while i < len(accounts):
            remove_empty_lines('locked_accounts.txt')
            remove_key_lines('locked_accounts.txt', 'POCKET')

            retry_count = 0
            i += 1
            success = False
            if is_account_locked(accounts[i - 1]):
                if i == len(accounts):
                    retry_count = 3
                else:
                    accounts.append(accounts[i - 1])
                    accounts.pop(i - 1)
                    print(accounts)
                    i -= 1
                # здесь выход в новую итерацию цикла со следующего элемента

            else:

                while retry_count < 3 and not success:
                    lock_account(accounts[i - 1], 'POCKET')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        time.sleep(2)
                        bot.send_message("https://t.me/poketkarmanfifi")
                        time.sleep(2)
                        bot.click_link()
                        time.sleep(2)
                        bot.click_launch_button()
                        bot.click_close_button()
                        bot.click_what_simple_action_button()
                        bot.click_start_mining_button()
                        bot.claim()
                        bot.daily()
                        time.sleep(2)
                        bot.claim()

                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i - 1], "POCKET")
                        sleep_time = random.randrange(5, 15)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 1 hour before restarting.")

        for hour in range(1):
            logging.info(f"Waiting... {1 - hour} hours left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()