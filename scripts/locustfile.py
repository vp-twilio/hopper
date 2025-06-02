from locust import HttpUser, task, between

class LocalTestUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def root(self):
        self.client.get("/")

    @task
    def api_data(self):
        self.client.get("/api/data")