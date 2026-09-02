from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Team, Task, Membership, Comment
from django.contrib.auth import get_user_model

User = get_user_model()

class TeamPermissionTests(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123')
        self.member = User.objects.create_user(username='member', password='pass123')
        self.outsider = User.objects.create_user(username='outsider', password='pass123')

        self.team = Team.objects.create(name='Engineering')
        Membership.objects.create(team=self.team, user=self.owner, role=Membership.Role.OWNER)
        Membership.objects.create(team=self.team, user=self.admin, role=Membership.Role.ADMIN)
        Membership.objects.create(team=self.team, user=self.member, role=Membership.Role.MEMBER)

        self.task = Task.objects.create(
            team=self.team,
            title='Fix login bug',
            created_by=self.owner,
            assignee=self.member,
        )

    def test_everyone_can_create_a_team(self):
        users = [self.outsider, self.member, self.admin, self.owner]
        url = "/api/teams/"

        for user in users:
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                response = self.client.post(
                    url,
                    {"name": f"new team {user.username}", "description": "new team"},
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_gets_404_on_team_detail_all_methods(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/teams/{self.team.pk}/"

        methods = {
            "get": self.client.get,
            "put": lambda u: self.client.put(u, {"name": "Changed", "description": "Changed"}),
            "patch": lambda u: self.client.patch(u, {"name": "Changed"}),
            "delete": self.client.delete,
        }

        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_can_view_team_detail(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/teams/{self.team.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_403_on_team_detail_edit_and_delete_methods(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/teams/{self.team.pk}/"

        methods = {
            "put": lambda u: self.client.put(u, {"name": "Changed", "description": "Changed"}),
            "patch": lambda u: self.client.patch(u, {"name": "Changed"}),
            "delete": self.client.delete,
        }

        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_200_on_team_detail_view_and_edit(self):
        self.client.force_authenticate(user=self.admin)
        url = f"/api/teams/{self.team.pk}/"

        methods = {
            "get": self.client.get,
            "put": lambda u: self.client.put(u, {"name": "Changed", "description": "Changed"}),
            "patch": lambda u: self.client.patch(u, {"name": "Changed"}),
        }

        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_gets_403_on_team_delete(self):
        self.client.force_authenticate(user=self.admin)
        url = f"/api/teams/{self.team.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_gets_200_on_team_detail_view_and_edit(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/"

        methods = {
            "get": self.client.get,
            "put": lambda u: self.client.put(u, {"name": "Changed", "description": "Changed"}),
            "patch": lambda u: self.client.patch(u, {"name": "Changed"}),
        }

        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_gets_204_on_team_delete(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    
class TaskPermissionTests(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123')
        self.member = User.objects.create_user(username='member', password='pass123')
        self.outsider = User.objects.create_user(username='outsider', password='pass123')

        self.team = Team.objects.create(name='Engineering')
        Membership.objects.create(team=self.team, user=self.owner, role=Membership.Role.OWNER)
        Membership.objects.create(team=self.team, user=self.admin, role=Membership.Role.ADMIN)
        Membership.objects.create(team=self.team, user=self.member, role=Membership.Role.MEMBER)

        self.task = Task.objects.create(
            team=self.team,
            title='Fix login bug',
            created_by=self.owner,
            assignee=self.member,
        )

        self.users = {
            "outsider": self.outsider,
            "member": self.member,
            "admin": self.admin,
            "owner": self.owner
        }
        self.members = [self.member, self.admin, self.owner]

        self.methods = {
            "get": self.client.get,
            "put": lambda u: self.client.put(
                u,
                {
                    "title": "new task",
                    "description": "new task",
                    "assignee": self.owner.pk,
                    "status": "todo"
                }
            ),
            "patch": lambda u: self.client.patch(u, {"title": "Changed"}),
            "delete": self.client.delete,
        }

    def test_members_gets_201_on_create_task(self):
        url = f"/api/teams/{self.team.pk}/tasks/"
        members = {self.users[k] for k in ["member", "admin", "owner"]}
        for user in members:
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                response = self.client.post(
                    url,
                    {
                        "title": "new task",
                        "description": "new task",
                        "assignee": user.pk,
                        "status": "todo"
                    }
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_gets_404_in_team_tasks_all_methods(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/tasks/{self.task.pk}/"

        for method_name, method_func in self.methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_gets_404_in_team_tasks_create(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/teams/{self.team.pk}/tasks/"
        response = self.client.post(
            url,
            {
                "title": "new task",
                "description": "new task",
                "assignee": self.outsider.pk,
                "status": "todo"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_gets_200_in_team_task_detail_view(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/tasks/{self.task.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_403_on_team_task_detail_edit_and_delete(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/tasks/{self.task.pk}/"

        methods = {k: self.methods[k] for k in ["put", "patch", "delete"]}

        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_and_owner_gets_200_team_tasks_view_and_edit(self):
        url = f"/api/tasks/{self.task.pk}/"
        members = {self.users[k] for k in ["admin", "owner"]}
        methods = {k: self.methods[k] for k in ["get", "put", "patch"]}
        for user in members:
            with self.subTest(user=user):
                for method_name, method_func in methods.items():
                    with self.subTest(method=method_name):
                        self.client.force_authenticate(user=user)
                        response = method_func(url)
                        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_gets_204_on_team_tasks_delete(self):
        url = f"/api/tasks/{self.task.pk}/"
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_owner_gets_204_on_team_tasks_delete(self):
        url = f"/api/tasks/{self.task.pk}/"
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_member_gets_200_on_edit_and_view_own_tasks(self):
        methods = {k: self.methods[k] for k in ["get", "put", "patch"]}
        self.client.force_authenticate(user=self.member)
        task = Task.objects.create(
            team=self.team,
            title='Fix login bug',
            created_by=self.member,
            assignee=self.member,
        )
        url = f"/api/tasks/{task.pk}/"
        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_204_on_delete_own_tasks(self):
        self.client.force_authenticate(user=self.member)
        task = Task.objects.create(
            team=self.team,
            title='Fix login bug',
            created_by=self.member,
            assignee=self.member,
        )
        url = f"/api/tasks/{task.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    