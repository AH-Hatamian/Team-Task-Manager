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

    def test_outsider_gets_404_in_team_tasks_view(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/teams/{self.team.pk}/tasks/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_member_gets_200_on_team_tasks_view(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/teams/{self.team.pk}/tasks/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

class MembershipsPermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123')
        self.member = User.objects.create_user(username='member', password='pass123')
        self.outsider = User.objects.create_user(username='outsider', password='pass123')
        self.admin2 = User.objects.create_user(username='admin2', password='pass123')
        self.testuser = User.objects.create_user(username='testuser', password='pass123')

        self.team = Team.objects.create(name='Engineering')
        self.admin_membership = Membership.objects.create(team=self.team, user=self.admin2, role=Membership.Role.ADMIN)
        self.owner_membership =Membership.objects.create(team=self.team, user=self.owner, role=Membership.Role.OWNER)
        Membership.objects.create(team=self.team, user=self.admin, role=Membership.Role.ADMIN)
        self.member_membership = Membership.objects.create(team=self.team, user=self.member, role=Membership.Role.MEMBER)

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
            "put": lambda u: self.client.put(u, {"role": Membership.Role.ADMIN}),
            "patch": lambda u: self.client.patch(u, {"role": Membership.Role.ADMIN}),
            "delete": self.client.delete,
        }
        
    def test_outsider_gets_404_in_all_methods(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.outsider)
        for method_name, method_func in self.methods.items():
            with self.subTest(method = method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_gets_404_on_create_membership(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(
            url,
            {
                "user": self.testuser.pk
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_gets_404_on_view_membership(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_gets_200_on_memberships_view(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.member)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_200_on_view_membership_detail(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.member)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_get_403_on_create_membership(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            url,
            {
                "user": self.testuser.pk
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_gets_403_on_membership_edit_and_delete(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.member)
        methods = {k: self.methods[k] for k in ["put", "patch", "delete"]}
        for method_name, method_func in methods.items():
            with self.subTest(method = method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_201_on_membership_create(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            url,
            {
                "user": self.testuser.pk
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_gets_200_on_memberships_view(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_gets_200_on_view_membership_detail(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_gets_403_on_membership_edit(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.admin)
        methods = {k: self.methods[k] for k in ["put", "patch"]}
        for method_name, method_func in methods.items():
            with self.subTest(method = method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_403_on_delete_admins_and_owner(self):
        self.client.force_authenticate(user=self.admin)
        urls = [
            f"/api/memberships/{self.admin_membership.pk}/",
            f"/api/memberships/{self.owner_membership.pk}/"
        ]
        for url in urls:
            with self.subTest(url = url):    
                response = self.client.delete(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_204_on_member_delete(self):
        self.client.force_authenticate(user=self.admin)
        url = f"/api/memberships/{self.member_membership.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_owner_gets_200_on_edit_membership(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.owner)
        
        methods = {k: self.methods[k] for k in ["put", "patch"]}
        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_gets_200_on_memberships_view(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_gets_200_on_view_membership_detail(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_gets_201_on_membership_create(self):
        url = f"/api/teams/{self.team.pk}/memberships/"
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            url,
            {
                "user": self.testuser.pk
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_gets_204_on_delete_members_and_admins(self):
        self.client.force_authenticate(user=self.owner)
        urls = [
            f"/api/memberships/{self.admin_membership.pk}/",
            f"/api/memberships/{self.member_membership.pk}/"
        ]
        for url in urls:
            with self.subTest(url = url):    
                response = self.client.delete(url)
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)        

    def test_owner_patch_actually_changes_role(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/memberships/{self.member_membership.pk}/"
        response = self.client.patch(url, {"role": Membership.Role.ADMIN})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, Membership.Role.ADMIN)

    def test_owner_put_actually_changes_role(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/memberships/{self.member_membership.pk}/"
        response = self.client.put(url, {"role": Membership.Role.ADMIN})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, Membership.Role.ADMIN)

    def test_admin_gets_400_when_adding_existing_member(self):
        self.client.force_authenticate(user=self.admin)
        url = f"/api/teams/{self.team.pk}/memberships/"
        response = self.client.post(url, {"user": self.member.pk})  
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_400_when_adding_existing_member(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/memberships/"
        response = self.client.post(url, {"user": self.member.pk})  
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_400_on_set_owner_memberships(self):
        url = f"/api/memberships/{self.member_membership.pk}/"
        self.client.force_authenticate(user=self.owner)
        methods = { 
            "put": lambda u: self.client.put(u, {"role": Membership.Role.OWNER}),
            "patch": lambda u: self.client.patch(u, {"role": Membership.Role.OWNER}),
        }        
        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_assignee_is_cleared_when_membership_deleted(self):
       
        task1 = Task.objects.create(
            team=self.team,
            title='Ghost Task 1',
            created_by=self.owner,
            assignee=self.member
        )
        task2 = Task.objects.create(
            team=self.team,
            title='Ghost Task 2',
            created_by=self.owner,
            assignee=self.member
        )

        self.client.force_authenticate(user=self.owner)
        url = f"/api/memberships/{self.member_membership.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        task1.refresh_from_db()
        task2.refresh_from_db()

        self.assertIsNone(task1.assignee)
        self.assertIsNone(task2.assignee)

class CommentPermissionTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123')
        self.member = User.objects.create_user(username='member', password='pass123')
        self.member2 = User.objects.create_user(username='member2', password='pass123')
        self.outsider = User.objects.create_user(username='outsider', password='pass123')

        self.team = Team.objects.create(name='Engineering')
        Membership.objects.create(team=self.team, user=self.owner, role=Membership.Role.OWNER)
        Membership.objects.create(team=self.team, user=self.admin, role=Membership.Role.ADMIN)
        Membership.objects.create(team=self.team, user=self.member, role=Membership.Role.MEMBER)
        Membership.objects.create(team=self.team, user=self.member2, role=Membership.Role.MEMBER)

        self.task = Task.objects.create(
            team=self.team,
            title='Fix login bug',
            created_by=self.owner,
            assignee=self.member,
        )


        self.comment_member = Comment.objects.create(author=self.member, task=self.task, body="test comment")
        self.comment_member2 = Comment.objects.create(author=self.member2, task=self.task, body="test comment 2")


        self.methods = {
            "get": self.client.get,
            "put": lambda u: self.client.put(u, {"body": "changed"}),
            "patch": lambda u: self.client.patch(u, {"body": "changed"}),
            "delete": self.client.delete,
        }


    def test_outsider_gets_404_in_task_comment_all_methods(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/comments/{self.comment_member2.pk}/"

        for method_name, method_func in self.methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_gets_404_in_comment_create(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/tasks/{self.task.pk}/comments/"
        response = self.client.post(url, {"body": "my comment"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_gets_404_on_comment_view(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/tasks/{self.task.pk}/comments/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_gets_201_in_comment_create(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/tasks/{self.task.pk}/comments/"
        response = self.client.post(url, {"body": "my comment"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_member_gets_200_on_comment_view(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/tasks/{self.task.pk}/comments/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_200_on_comment_detail_view(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/comments/{self.comment_member2.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_403_on_comments_edit_and_delete(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/comments/{self.comment_member2.pk}/"
        methods = {k: self.methods[k] for k in ["put", "patch", "delete"]}
        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_and_owner_gets_201_in_comment_create(self):
        url = f"/api/tasks/{self.task.pk}/comments/"
        users = [self.admin, self.owner]
        for user in users:
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                response = self.client.post(url, {"body": "my comment"})
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_and_owner_gets_200_on_comment_view(self):
        url = f"/api/tasks/{self.task.pk}/comments/"
        users = [self.admin, self.owner]
        for user in users:
            with self.subTest(user=user):       
                self.client.force_authenticate(user=user)
                
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_and_owner_gets_200_on_comment_detail_view(self):
        url = f"/api/comments/{self.comment_member2.pk}/"
        users = [self.admin, self.owner]
        for user in users:
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_and_owner_gets_403_on_comments_edit(self):
        url = f"/api/comments/{self.comment_member2.pk}/"
        users = [self.admin, self.owner]
        for user in users:
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                methods = {k: self.methods[k] for k in ["put", "patch"]}
                for method_name, method_func in methods.items():
                    with self.subTest(method=method_name):
                        response = method_func(url)
                        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_gets_204_on_comment_delete(self):
        url = f"/api/comments/{self.comment_member2.pk}/"
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_gets_204_on_comment_delete(self):
        url = f"/api/comments/{self.comment_member2.pk}/"
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_member_gets_200_on_edit_own_comments(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/comments/{self.comment_member.pk}/"
        methods = {k: self.methods[k] for k in ["put", "patch"]}
        for method_name, method_func in methods.items():
            with self.subTest(method=method_name):
                response = method_func(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_gets_204_on_delete_own_comments(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/comments/{self.comment_member.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_member_patch_actually_changes_comment_body(self):
        self.client.force_authenticate(user=self.member)
        url = f"/api/comments/{self.comment_member.pk}/"
        response = self.client.patch(url, {"body": "changed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment_member.refresh_from_db()
        self.assertEqual(self.comment_member.body, "changed")

class TransferOwnershipPermissionTest(APITestCase):
    def setUp(self):

        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123')
        self.member = User.objects.create_user(username='member', password='pass123')
        self.outsider = User.objects.create_user(username='outsider', password='pass123')

        self.team = Team.objects.create(name='Engineering')
        self.owner_membership = Membership.objects.create(team=self.team, user=self.owner, role=Membership.Role.OWNER)
        self.admin_membership = Membership.objects.create(team=self.team, user=self.admin, role=Membership.Role.ADMIN)
        self.member_membership = Membership.objects.create(team=self.team, user=self.member, role=Membership.Role.MEMBER)

        self.method = {"new_owner": self.admin.pk}
        


    def test_outsider_gets_404_on_transfer(self):
        self.client.force_authenticate(user=self.outsider)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, self.method)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_and_admin_gets_404_on_transfer(self):
        roles = [self.member, self.admin]
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        for role in roles:
            with self.subTest(user=role):
                self.client.force_authenticate(user=role)
                response = self.client.post(url, self.method)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_gets_400_when_target_is_not_admin(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, {"new_owner": self.member.pk})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_400_when_target_is_not_a_member(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, {"new_owner": self.outsider.pk})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_400_when_transferring_to_self(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, {"new_owner": self.owner.pk})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_200_on_transfer_admin(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, self.method)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_actually_transfer_ownership(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response =self.client.post(url, self.method)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner_membership.refresh_from_db()
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.role, Membership.Role.ADMIN)
        self.assertEqual(self.admin_membership.role, Membership.Role.OWNER)

    def test_owner_gets_400_when_new_owner_missing(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_400_when_new_owner_id_invalid(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/teams/{self.team.pk}/transfer-ownership/"
        response = self.client.post(url, {"new_owner": 99999})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_gets_403_when_deleting_own_membership(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/memberships/{self.owner_membership.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
