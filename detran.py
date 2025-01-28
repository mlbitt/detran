from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.webdriver.support.expected_conditions as EC
import yaml
from selenium.common.exceptions import NoSuchElementException
from retry import retry
from capsolver_extension_python import Capsolver
import re
from time import sleep

class Detran():
    def __init__(self) -> None:
        self.selectors = yaml.load(open('selectors.yaml'), Loader=yaml.FullLoader)
        self.urls = yaml.load(open('urls.yaml'), Loader=yaml.FullLoader)

    
    def __validate_consulta_patio_params(self, municipio=None, chassi=None, placa=None) -> None:
        assert municipio or chassi or placa, "At least one of the following parameters must be provided: municipio, chassi, placa"

    def __fill_consulta_patio_form(self, wait, municipio=None, chassi=None, placa=None):
        print("Filling 'consulta_patio' form")
        if municipio:
            print(f"\tSetting 'municipio' to '{municipio}'")
            wait.until(EC.element_to_be_clickable(self.selectors['consulta_patio']['input_municipio'])).send_keys(municipio)
        if placa:
            print(f"\tSetting 'placa' to '{placa}'")
            wait.until(EC.element_to_be_clickable(self.selectors['consulta_patio']['input_placa'])).send_keys(placa)
        if chassi:
            print(f"\tSetting 'chassi' to '{chassi}'")
            wait.until(EC.element_to_be_clickable(self.selectors['consulta_patio']['input_chassi'])).send_keys(chassi)


    def __set_capsolver_extension(self, capsolver_token) -> None:
        return Capsolver(
            api_key=capsolver_token
        ).load()
    

    def __wait_for_captcha_solved(self, driver, wait) -> None:
        print("Waiting for captcha to be solved")
        captcha_iframe_element = wait.until(EC.presence_of_element_located(self.selectors['consulta_patio']['iframe_recaptcha']))
        driver.switch_to.frame(captcha_iframe_element)
        wait.until(EC.visibility_of_element_located(self.selectors['consulta_patio']['span_captcha_solved']))
        driver.switch_to.default_content()


    def __submit_consulta_patio_form(self, wait) -> None:
        print("Submitting 'consulta_patio' form")
        wait.until(EC.element_to_be_clickable(self.selectors['consulta_patio']['button_submit'])).click()


    def __get_consulta_patio_return(self, driver):
        print("Getting 'consulta_patio' return")

        for i in range(60):
            try:
                results_str = driver.find_element(*self.selectors['consulta_patio']['tbody_results']).text
              
                match = re.search(r'(\d+)\s+(\w+)\s+(\d{2}/\d{2}/\d{4})\s+(.+?)\s+R\$\s+([\d,.]+)', results_str)
                if match:
                    return {
                        'number': match.group(1),
                        'placa': match.group(2),
                        'date': match.group(3),
                        'company': match.group(4),
                        'amount': match.group(5)
                    }
            except NoSuchElementException:
                pass

            try:
                no_results_text = driver.find_element(*self.selectors['consulta_patio']['label_no_results']).text
                print(f"No results found. {no_results_text}")
                return None
            except NoSuchElementException:
                pass

            sleep(0.5)
        else:
            raise Exception("Timeout waiting for 'consulta_patio' return")

    @retry(tries=3, delay=1, backoff=2)
    def consulta_patio(self, capsolver_token, municipio=None, chassi=None, placa=None) -> dict:
        self.__validate_consulta_patio_params(municipio, chassi, placa)

        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument(self.__set_capsolver_extension(capsolver_token))
        options.add_argument("--no-sandbox") 
        options.accept_insecure_certs = True 
        options.add_argument(f"--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")  
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-infobars") 
        options.add_argument("--disable-notifications") 
        options.page_load_strategy = "eager"

        driver =  webdriver.Chrome(options=options)
        try:
            wait = WebDriverWait(driver, 45)

            driver.get(self.urls['consulta_patio'])

            self.__fill_consulta_patio_form(wait, municipio, chassi, placa)

            self.__wait_for_captcha_solved(driver, wait)
            
            self.__submit_consulta_patio_form(wait)

            return self.__get_consulta_patio_return(driver)
        except Exception as e:
            print(e)
            raise
        finally:
            driver.quit()