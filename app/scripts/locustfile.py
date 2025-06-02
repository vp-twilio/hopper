from locust import HttpUser, task

class DummyUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")