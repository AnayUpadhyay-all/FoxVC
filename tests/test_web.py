import unittest
from engine.web import WebApplication, WebElement
from engine.runner import run_foxvc, run_foxvc_project

class TestFoxVCWebRuntime(unittest.TestCase):
    def test_web_element_creation_and_html(self):
        el = WebElement("div", "Hello Web", {"class": "card", "id": "main"})
        html = el.to_html()
        self.assertIn("<div", html)
        self.assertIn('class="card"', html)
        self.assertIn("Hello Web</div>", html)

    def test_web_element_children_hierarchy(self):
        parent = WebElement("div")
        child1 = WebElement("h1", "Title")
        child2 = WebElement("p", "Paragraph")
        parent.add_child(child1)
        parent.add_child(child2)
        html = parent.to_html()
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<p>Paragraph</p>", html)

    def test_web_application_mounting(self):
        app = WebApplication("Dashboard")
        el = WebElement("section", "Content")
        app.mount(el)
        self.assertEqual(len(app.root_elements), 1)
        self.assertIn("<section>Content</section>", app.render())

    def test_web_app_state_management(self):
        app = WebApplication()
        app.set_state("temperature", 350)
        self.assertEqual(app.get_state("temperature"), 350)
        self.assertIsNone(app.get_state("pressure"))
        self.assertEqual(app.get_state("pressure", 1013), 1013)

    def test_web_app_register_action(self):
        app = WebApplication()
        app.register_action("cooldown", "temperature", "set", 200)
        self.assertIn("cooldown", app.actions)
        self.assertEqual(app.actions["cooldown"]["target"], "temperature")

    def test_web_app_bind_and_dispatch_event_set(self):
        app = WebApplication()
        app.set_state("volume", 50)
        app.bind_event("btn_mute", "click", "volume", "set", 0)
        app.dispatch_event("btn_mute", "click")
        self.assertEqual(app.get_state("volume"), 0)

    def test_web_app_dispatch_event_toggle(self):
        app = WebApplication()
        app.set_state("light", False)
        app.bind_event("btn_switch", "click", "light", "toggle")
        app.dispatch_event("btn_switch", "click")
        self.assertTrue(app.get_state("light"))
        app.dispatch_event("btn_switch", "click")
        self.assertFalse(app.get_state("light"))

    def test_web_app_dispatch_action_by_name(self):
        app = WebApplication()
        app.set_state("speed", 100)
        app.register_action("stop", "speed", "set", 0)
        app.bind_event("btn_stop", "click", "speed", "stop")
        app.dispatch_event("btn_stop", "click")
        self.assertEqual(app.get_state("speed"), 0)

    def test_element_visibility_toggle(self):
        el = WebElement("div", "Secret")
        self.assertIn("Secret", el.to_html())
        el.visible = False
        self.assertEqual(el.to_html(), "")

    def test_automatic_web_app_discovery_without_render(self):
        code = '''state pressure = 1013
app = element "div"
mount app
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertIsNotNone(res.web_app)
        self.assertEqual(res.web_app.get_state("pressure"), 1013)

    def test_interactive_app_fox_example(self):
        res = run_foxvc_project("examples/interactive_app.fox")
        self.assertTrue(res.success, res.error)
        self.assertIsNotNone(res.web_app)
        self.assertEqual(res.web_app.get_state("reactor_temp"), 320)
        self.assertEqual(res.web_app.get_state("status_message"), "Normal")

    def test_web_output_population(self):
        code = '''app = element "div" "Live Console"
mount app
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertIn("Live Console", res.web_output)

    def test_state_statement_in_interpreter(self):
        code = 'state status = "Active"\nsay status'
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "Active")

    def test_action_and_event_binding_script(self):
        code = '''state counter = 0
action add_one counter set 1
bind "btn" "click" "counter" "add_one"
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        app = res.web_app
        app.dispatch_event("btn", "click")
        self.assertEqual(app.get_state("counter"), 1)

    def test_show_statement_lifecycle(self):
        code = '''panel = element "section" "Settings"
show panel
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertIn("Settings", res.web_output)

if __name__ == '__main__':
    unittest.main()
