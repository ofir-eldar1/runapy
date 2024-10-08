import pytest
import json
from unittest.mock import Mock, patch

from runai import models
from runai import errors
from runai import controllers
from runai.client import RunaiClient


class TestProjectController:
    @pytest.fixture
    def mock_client(self):
        client = Mock()
        client.cluster_id = "71f69d83-ba66-4822-adf8-55ce55efd219"
        return client

    @pytest.fixture
    def controller(self, mock_client):
        return controllers.ProjectController(mock_client)

    def test_init(self, mock_client):
        controller = controllers.ProjectController(mock_client)
        assert controller.client == mock_client

    def test_init_missing_cluster_id(self):
        with patch("runai.client.RunaiClient._generate_api_token", return_value="token"):
            with patch("runai.client.RunaiClient._set_token_expiary", return_value="1727185600"):
                client = RunaiClient(
                    client_id="api-client",
                    client_secret="test-client-secret",
                    runai_base_url="https://test.runai.ai"
                )
        with pytest.raises(errors.RunaiClusterIDNotConfigured) as exc_info:
            controllers.ProjectController(client)
        assert "cluster_id is not configured" in str(exc_info)

    def test_all(self, controller):
        mock_response = [{"id": 1, "name": "project1"}, {"id": 2, "name": "project2"}]
        controller.client.get.return_value = mock_response

        result = controller.all()

        assert result == mock_response
        controller.client.get.assert_called_once_with(
            "/api/v1/org-unit/projects", models.ProjectQueryParams()
        )

    def test_all_with_params(self, controller):
        mock_response = [{"id": 1, "name": "project1"}]
        controller.client.get.return_value = mock_response

        result = controller.all(
            filterBy="name==project1", sortBy="name", sortOrder="asc", limit=1
        )

        assert result == mock_response
        controller.client.get.assert_called_once_with(
            "/api/v1/org-unit/projects",
            models.ProjectQueryParams(
                filterBy="name==project1", sortBy="name", sortOrder="asc", limit=1
            ),
        )

    def test_all_with_bad_params(self, controller):
        with pytest.raises(errors.RunaiQueryParamsError) as exc_info:
            controller.all(
                filterBy="name==project1", sortBy="name", sortOrder="NONE", limit="1"
            )
        assert "Failed to build query parameters" in str(exc_info)
        controller.client.get.assert_not_called()

        with pytest.raises(errors.RunaiQueryParamsError) as exc_info:
            controller.all(
                filterBy="name==project1", sortBy="NONE", sortOrder="asc", limit="1"
            )
        assert "Failed to build query parameters" in str(exc_info)
        controller.client.get.assert_not_called()

    def test_create(self, controller):
        project_name = "new_project"
        mock_response = {"id": 3, "name": project_name}
        controller.client.post.return_value = mock_response

        resources = [
            {
                "nodePool": {"id": "1", "name": "default"},
                "gpu": {"deserved": 1, "limit": 2, "overQuotaWeight": 1},
                "cpu": None,
                "memory": None,
            }
        ]
        requested_namespace = "test-namespace"
        default_node_pools = ["default"]
        scheduling_rules = {
            "interactiveJobTimeLimitSeconds": 3600,
            "interactiveJobMaxIdleDurationSeconds": None,
            "interactiveJobPreemptIdleDurationSeconds": None,
            "trainingJobTimeLimitSeconds": None,
            "trainingJobMaxIdleDurationSeconds": None,
        }
        parent_id = "parent1"
        node_types = {"training": ["gpu"], "workspace": ["cpu"]}

        expected_body = {
            "name": project_name,
            "clusterId": controller.client.cluster_id,
            "resources": resources,
            "nodeTypes": node_types,
            "defaultNodePools": default_node_pools,
            "schedulingRules": scheduling_rules,
            "requestedNamespace": requested_namespace,
            "parentId": parent_id,
        }

        expected_body = json.dumps(expected_body).replace(" ", "")

        result = controller.create(
            name=project_name,
            resources=resources,
            requested_namespace=requested_namespace,
            default_node_pools=default_node_pools,
            scheduling_rules=scheduling_rules,
            parent_id=parent_id,
            node_types=node_types,
        )

        assert result == mock_response
        controller.client.post.assert_called_once_with(
            "/api/v1/org-unit/projects", expected_body
        )

    def test_create_empty_resources(self, controller):
        with pytest.raises(errors.RunaiBuildModelError) as exc_info:
            controller.create(
                name="new_project",
                resources=[{}],
                requested_namespace="test-namespace",
                default_node_pools=["default"],
                scheduling_rules=models.SchedulingRules(
                    interactiveJobTimeLimitSeconds=3600
                ),
                parent_id="parent1",
                node_types=models.NodeTypes(training=["gpu"], workspace=["cpu"]),
            )
        assert "Failed to build body scheme" in str(exc_info)
        controller.client.post.assert_not_called()

    def test_get(self, controller):
        project_id = 1
        mock_response = {"id": project_id, "name": "project1"}
        controller.client.get.return_value = mock_response

        result = controller.get(project_id=project_id)

        assert result == mock_response
        controller.client.get.assert_called_once_with(
            f"/api/v1/org-unit/projects/{project_id}"
        )

    def test_update(self, controller):
        project_id = 10
        mock_response = {"id": project_id, "name": "updated_project"}
        controller.client.put.return_value = mock_response
        resources = [
            {
                "nodePool": {"id": "1", "name": "default"},
                "gpu": {"deserved": 1, "limit": 2, "overQuotaWeight": 1},
                "cpu": None,
                "memory": None,
            }
        ]
        default_node_pools = ["default", "gpu"]
        scheduling_rules = {
            "interactiveJobTimeLimitSeconds": 7200,
            "interactiveJobMaxIdleDurationSeconds": None,
            "interactiveJobPreemptIdleDurationSeconds": None,
            "trainingJobTimeLimitSeconds": None,
            "trainingJobMaxIdleDurationSeconds": None,
        }
        node_types = {"training": ["gpu"], "workspace": ["cpu"]}

        expected_body = {
            "resources": resources,
            "nodeTypes": node_types,
            "defaultNodePools": default_node_pools,
            "schedulingRules": scheduling_rules,
        }
        expected_body = json.dumps(expected_body).replace(" ", "")

        result = controller.update(
            project_id=project_id,
            resources=resources,
            default_node_pools=default_node_pools,
            node_types=node_types,
            scheduling_rules=scheduling_rules,
        )

        assert result == mock_response
        controller.client.put.assert_called_once_with(
            f"/api/v1/org-unit/projects/{project_id}", expected_body
        )

    def test_update_missing_resources(self, controller):
        with pytest.raises(errors.RunaiBuildModelError) as exc_info:
            controller.update(
                project_id=1,
                resources={},
            )
        assert "Failed to build body scheme" in str(exc_info)
        controller.client.put.assert_not_called()

    def test_delete(self, controller):
        project_id = 1
        mock_response = {"status code": 202, "message": "Accepted"}
        controller.client.delete.return_value = mock_response

        result = controller.delete(project_id=project_id)

        assert result == mock_response
        controller.client.delete.assert_called_once_with(
            f"/api/v1/org-unit/projects/{project_id}"
        )

    def test_patch_resources_missing_required_gpu(self, controller):
        with pytest.raises(errors.RunaiBuildModelError) as exc_info:
            controller.patch(
                project_id=1,
                resources={
                    "nodePool": {
                        "id": "1",
                        "name": "default",
                    },
                })
        assert "Failed to build body scheme" in str(exc_info)
        controller.client.patch.assert_not_called()
