# polls/tests.py

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.contrib.auth.models import User # Importante para crear el superusuario

from selenium import webdriver
from selenium.webdriver.firefox.options import Options # Para el modo headless
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Importamos los modelos para poder verificar (pero no para crear)
from .models import Question, Choice 

class PollsAdminSeleniumTests(StaticLiveServerTestCase):
    """
    Pruebas End-to-End siguiendo las especificaciones de la EAC.
    El WebDriver se inicializa en setUpClass.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Configuración de la CLASE (se ejecuta 1 sola vez).
        Inicializa el navegador y crea el superusuario de prueba.
        """
        super().setUpClass() # Llama al setUpClass padre (levanta el servidor)
        
        # 1. Configura el WebDriver (navegador)
        opts = Options()
        opts.add_argument("--headless") # Modo sin interfaz gráfica
        cls.selenium = webdriver.Firefox(options=opts)
        cls.selenium.implicitly_wait(5) # Espera implícita

        # 2. Crea el superusuario (siguiendo el método exacto del profesor)
        user = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        user.is_superuser = True
        user.is_staff = True
        user.save()

        # 3. Crea el nou usuari STAFF sense permisos
        staff_user = User.objects.create_user("staff_user", "staff@test.com", "password123")
        staff_user.is_staff = True
        staff_user.save()

    @classmethod
    def tearDownClass(cls):
        """
        Limpieza de la CLASE (se ejecuta 1 sola vez al final).
        Cierra el navegador.
        """
        cls.selenium.quit()
        super().tearDownClass() # Llama al tearDownClass padre (apaga el servidor)

    def test_admin_full_workflow(self):
        """
        Test que simula el flujo completo:
        Login -> Crear Question -> Crear Choice
        
        Usa 'self.selenium' y 'self.live_server_url' (heredados de la clase)
        """
        
        # --- 1. Login ---
        # self.live_server_url apunta al servidor de prueba
        self.selenium.get(self.live_server_url + '/admin/')
        
        # Rellenar formulario de login
        self.selenium.find_element(By.ID, "id_username").send_keys("isard")
        self.selenium.find_element(By.ID, "id_password").send_keys("pirineus")
        self.selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        # Verificar que estamos en el admin (buscamos el título)
        wait = WebDriverWait(self.selenium, 10)
        wait.until(EC.title_contains("Site administration"))

        # --- 2. Ir a Questions y crear una ---
        # Hacemos clic en el enlace 'Questions'
        self.selenium.find_element(By.XPATH, "//a[contains(text(), 'Questions')]").click()
        
        # Clic en "Add question"
        self.selenium.find_element(By.CLASS_NAME, "addlink").click()
        
        # Rellenar formulario de Question
        wait.until(EC.presence_of_element_located((By.ID, "id_question_text")))
        self.selenium.find_element(By.ID, "id_question_text").send_keys("Question de test Selenium?")
        
        # Rellenar fecha y hora (clic en 'Today' y 'Now')
        self.selenium.find_element(By.LINK_TEXT, "Today").click()
        self.selenium.find_element(By.LINK_TEXT, "Now").click()
        
        # Guardar
        self.selenium.find_element(By.NAME, "_save").click()
        
        # --- 3. Verificar creación de Question ---
        # Verificar que volvimos a la lista y el mensaje de éxito existe
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "success")))
        
        # Verificamos que el objeto existe en la BBDD
        # (Aquí SÍ podemos usar Python, solo para verificar)
        self.assertTrue(Question.objects.filter(question_text="Question de test Selenium?").exists())
        
        # Guardamos la question creada para usarla después
        created_question = Question.objects.get(question_text="Question de test Selenium?")

        # --- 4. Ir a Choices y crear uno ---
        # Volvemos al home del admin
        self.selenium.find_element(By.LINK_TEXT, "Home").click()
        
        # Clic en 'Choices'
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Choices')]")))
        self.selenium.find_element(By.XPATH, "//a[contains(text(), 'Choices')]").click()
        
        # Clic en "Add choice"
        self.selenium.find_element(By.CLASS_NAME, "addlink").click()

        # Rellenar formulario de Choice
        wait.until(EC.presence_of_element_located((By.ID, "id_choice_text")))
        self.selenium.find_element(By.ID, "id_choice_text").send_keys("Choice de test Selenium")
        self.selenium.find_element(By.ID, "id_votes").send_keys("0")

        # Seleccionar la Question del desplegable
        select_question = Select(self.selenium.find_element(By.ID, "id_question"))
        select_question.select_by_value(str(created_question.pk))

        # Guardar
        self.selenium.find_element(By.NAME, "_save").click()

        # --- 5. Verificar creación de Choice ---
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "success")))
        
        # Verificamos en la BBDD
        self.assertTrue(Choice.objects.filter(choice_text="Choice de test Selenium").exists())
        
        # Verificamos que está bien asociada
        created_choice = Choice.objects.get(choice_text="Choice de test Selenium")
        self.assertEqual(created_choice.question, created_question)
        
        print("\nTest de Selenium (Patrón Profesor) completado con éxito.")




    def test_staff_user_no_permissions(self):
        """
        Verifica que un usuario 'staff' sense permisos no pot veure els models 'Questions' o 'Choices' en el admin.
        """
        # Necesitamos importar la excepción
        from selenium.common.exceptions import NoSuchElementException

        # --- 1. Login como staff_user ---
        self.selenium.get(self.live_server_url + '/admin/')
        
        self.selenium.find_element(By.ID, "id_username").send_keys("staff_user")
        self.selenium.find_element(By.ID, "id_password").send_keys("password123")
        self.selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        # Verificar que estamos en el admin
        wait = WebDriverWait(self.selenium, 10)
        wait.until(EC.title_contains("Site administration"))
        
        # --- 2. Verificar que NO ve 'Questions' ---
        # Usamos el patrón "try/except" del profesor
        try:
            # Buscamos el enlace por su texto
            self.selenium.find_element(By.XPATH, "//a[contains(text(), 'Questions')]")
            # Si lo encuentra, forzamos el fallo del test
            assert False, "Error: El usuario ve 'Questions', pero NO debería."
        except NoSuchElementException:
            # Éxito: El elemento no se encontró, que es lo esperado.
            pass

        # --- 3. Verificar que NO ve 'Choices' ---
        try:
            self.selenium.find_element(By.XPATH, "//a[contains(text(), 'Choices')]")
            assert False, "Error: El usuario ve 'Choices', pero NO debería."
        except NoSuchElementException:
            # Éxito: El elemento no se encontró.
            pass
            
        print("\nTest de permisos de staff (sin perms) completado con éxito.")
