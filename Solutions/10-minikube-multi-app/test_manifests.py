"""Cross-checks the Kubernetes manifests against each other and against the scripts.

Uses miniyaml.py (PyYAML is not installed). These are static checks: they catch
the class of mistakes that make a cluster apply succeed but the app not work,
such as a Service whose selector matches nothing or lives in another namespace.
They do not talk to a cluster and cannot prove the manifests are accepted by the API server.
"""
import pathlib
import re
import unittest

from miniyaml import load_all

ROOT = pathlib.Path(__file__).parent
NAMESPACE = "lab10"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def load_manifests():
    docs = []
    for path in sorted((ROOT / "k8s").glob("*.yaml")):
        for doc in load_all(path.read_text(encoding="utf-8")):
            docs.append((path.name, doc))
    return docs


MANIFESTS = load_manifests()


def of_kind(kind):
    return [d for _, d in MANIFESTS if d["kind"] == kind]


def deployment(name):
    return next(d for d in of_kind("Deployment") if d["metadata"]["name"] == name)


def pod_spec(dep):
    return dep["spec"]["template"]["spec"]


def pod_labels(dep):
    return dep["spec"]["template"]["metadata"]["labels"]


class StructureTests(unittest.TestCase):
    def test_every_resource_has_required_fields(self):
        for fname, doc in MANIFESTS:
            for field in ("apiVersion", "kind", "metadata"):
                self.assertIn(field, doc, f"{fname}: missing {field}")
            self.assertTrue(doc["metadata"].get("name"), f"{fname}: missing name")

    def test_all_namespaced_resources_use_the_lab_namespace(self):
        for fname, doc in MANIFESTS:
            if doc["kind"] == "Namespace":
                self.assertEqual(doc["metadata"]["name"], NAMESPACE)
            else:
                self.assertEqual(doc["metadata"].get("namespace"), NAMESPACE,
                                 f"{fname}: {doc['kind']}/{doc['metadata']['name']} namespace")

    def test_namespace_is_applied_first(self):
        names = [p.name for p in sorted((ROOT / "k8s").glob("*.yaml"))]
        self.assertEqual(names[0], "00-namespace.yaml")

    def test_no_duplicate_resources(self):
        keys = [(d["kind"], d["metadata"]["name"]) for _, d in MANIFESTS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_expected_inventory(self):
        self.assertEqual(
            sorted((d["kind"], d["metadata"]["name"]) for _, d in MANIFESTS),
            sorted([
                ("Namespace", "lab10"),
                ("Deployment", "product-catalog"), ("Service", "product-catalog"),
                ("PodDisruptionBudget", "product-catalog"),
                ("Deployment", "shopping-cart"), ("Service", "shopping-cart"),
                ("PodDisruptionBudget", "shopping-cart"),
                ("Deployment", "redis"), ("Service", "redis"),
            ]))


class DeploymentTests(unittest.TestCase):
    def test_replica_counts(self):
        self.assertEqual(deployment("product-catalog")["spec"]["replicas"], 2)
        self.assertEqual(deployment("shopping-cart")["spec"]["replicas"], 3)
        self.assertEqual(deployment("redis")["spec"]["replicas"], 1)

    def test_selector_matches_pod_template_labels(self):
        for dep in of_kind("Deployment"):
            selector = dep["spec"]["selector"]["matchLabels"]
            labels = pod_labels(dep)
            for key, value in selector.items():
                self.assertEqual(labels.get(key), value, dep["metadata"]["name"])

    def test_probes_target_the_container_port(self):
        for dep in of_kind("Deployment"):
            for container in pod_spec(dep)["containers"]:
                ports = [p["containerPort"] for p in container["ports"]]
                for probe_name in ("readinessProbe", "livenessProbe"):
                    probe = container[probe_name]
                    target = (probe.get("httpGet") or probe.get("tcpSocket"))["port"]
                    self.assertIn(target, ports, f"{container['name']} {probe_name}")

    def test_http_probe_paths_exist_in_the_apps(self):
        sources = {
            "product-catalog": read("apps/product-catalog/app.py"),
            "shopping-cart": read("apps/shopping-cart/app.py"),
        }
        for name, source in sources.items():
            container = pod_spec(deployment(name))["containers"][0]
            for probe in ("readinessProbe", "livenessProbe"):
                path = container[probe]["httpGet"]["path"]
                self.assertIn(f'"{path}"', source, f"{name} {probe} path {path}")

    def test_every_container_has_requests_and_limits(self):
        for dep in of_kind("Deployment"):
            for container in pod_spec(dep)["containers"]:
                for section in ("requests", "limits"):
                    for resource in ("cpu", "memory"):
                        self.assertIn(resource, container["resources"][section],
                                      f"{container['name']} {section}.{resource}")

    def test_run_as_non_root_with_numeric_user(self):
        for dep in of_kind("Deployment"):
            ctx = pod_spec(dep)["securityContext"]
            self.assertIs(ctx["runAsNonRoot"], True)
            self.assertIsInstance(ctx["runAsUser"], int)
            self.assertGreater(ctx["runAsUser"], 0)

    def test_containers_drop_privileges(self):
        for dep in of_kind("Deployment"):
            for container in pod_spec(dep)["containers"]:
                ctx = container["securityContext"]
                self.assertIs(ctx["allowPrivilegeEscalation"], False)
                self.assertEqual(ctx["capabilities"]["drop"], ["ALL"])

    def test_app_images_are_local_only_and_pinned(self):
        for name in ("product-catalog", "shopping-cart"):
            container = pod_spec(deployment(name))["containers"][0]
            self.assertEqual(container["image"], f"lab10/{name}:1.0")
            self.assertEqual(container["imagePullPolicy"], "Never")
        redis_image = pod_spec(deployment("redis"))["containers"][0]["image"]
        self.assertRegex(redis_image, r":\d+\.\d+")  # pinned, not :latest

    def test_app_user_matches_dockerfile_uid(self):
        for name in ("product-catalog", "shopping-cart"):
            uid = pod_spec(deployment(name))["securityContext"]["runAsUser"]
            self.assertIn(f"--uid {uid}", read(f"apps/{name}/Dockerfile"))
            self.assertIn(f"USER {uid}", read(f"apps/{name}/Dockerfile"))


class ServiceTests(unittest.TestCase):
    def backing_deployment(self, svc):
        """Deployments in the Service's own namespace whose pods its selector matches."""
        ns = svc["metadata"]["namespace"]
        selector = svc["spec"]["selector"]
        return [d for d in of_kind("Deployment")
                if d["metadata"].get("namespace") == ns
                and all(pod_labels(d).get(k) == v for k, v in selector.items())]

    def test_every_service_selects_pods_in_its_namespace(self):
        for svc in of_kind("Service"):
            self.assertEqual(len(self.backing_deployment(svc)), 1, svc["metadata"]["name"])

    def test_target_port_is_a_container_port_of_the_backing_pods(self):
        for svc in of_kind("Service"):
            dep, = self.backing_deployment(svc)
            ports = [p["containerPort"] for c in pod_spec(dep)["containers"] for p in c["ports"]]
            for port in svc["spec"]["ports"]:
                self.assertIn(port["targetPort"], ports, svc["metadata"]["name"])

    def test_service_types(self):
        types = {s["metadata"]["name"]: s["spec"]["type"] for s in of_kind("Service")}
        self.assertEqual(types, {"product-catalog": "NodePort", "shopping-cart": "NodePort",
                                 "redis": "ClusterIP"})

    def test_cart_points_at_the_redis_service(self):
        env = pod_spec(deployment("shopping-cart"))["containers"][0]["env"]
        host = next(e["value"] for e in env if e["name"] == "REDIS_HOST")
        redis_services = [s for s in of_kind("Service") if s["metadata"]["name"] == host]
        self.assertEqual(len(redis_services), 1, f"no Service named {host}")
        redis_port = redis_services[0]["spec"]["ports"][0]["port"]
        self.assertEqual(redis_port, 6379)  # cart_store.py default port


class AvailabilityTests(unittest.TestCase):
    def test_replicas_are_spread_across_nodes(self):
        for name in ("product-catalog", "shopping-cart"):
            dep = deployment(name)
            constraints = pod_spec(dep)["topologySpreadConstraints"]
            self.assertEqual(len(constraints), 1)
            spread = constraints[0]
            self.assertEqual(spread["topologyKey"], "kubernetes.io/hostname")
            self.assertEqual(spread["maxSkew"], 1)
            for key, value in spread["labelSelector"]["matchLabels"].items():
                self.assertEqual(pod_labels(dep)[key], value)

    def test_spread_does_not_block_scheduling_when_a_node_is_lost(self):
        for name in ("product-catalog", "shopping-cart"):
            spread = pod_spec(deployment(name))["topologySpreadConstraints"][0]
            self.assertEqual(spread["whenUnsatisfiable"], "ScheduleAnyway")

    def test_disruption_budgets_match_pods_and_leave_room_to_drain(self):
        for pdb in of_kind("PodDisruptionBudget"):
            name = pdb["metadata"]["name"]
            dep = deployment(name)
            for key, value in pdb["spec"]["selector"]["matchLabels"].items():
                self.assertEqual(pod_labels(dep)[key], value)
            minimum = pdb["spec"]["minAvailable"]
            self.assertGreaterEqual(minimum, 1)
            self.assertLess(minimum, dep["spec"]["replicas"],
                            f"{name}: PDB would block every drain")


class ScriptConsistencyTests(unittest.TestCase):
    def test_deploy_builds_and_loads_the_images_the_manifests_use(self):
        deploy = read("deploy.sh")
        for name in ("product-catalog", "shopping-cart"):
            image = pod_spec(deployment(name))["containers"][0]["image"]
            self.assertIn(image, deploy, f"deploy.sh never mentions {image}")
            self.assertIn(f"apps/{name}", deploy)

    def test_scripts_get_namespace_and_profile_from_lib(self):
        self.assertIn("NS=lab10", read("lib.sh"))
        self.assertIn("PROFILE=lab10", read("lib.sh"))
        for rel in ("deploy.sh", "verify.sh", "scale.sh", "failover.sh", "cleanup.sh"):
            self.assertIn(". ./lib.sh", read(rel), f"{rel} does not source lib.sh")

    def test_no_script_runs_kubectl_without_the_pinned_context(self):
        """Every kubectl call must go through k()/kc() so it cannot hit another cluster."""
        for path in ROOT.glob("*.sh"):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if path.name == "lib.sh" or code.strip().startswith("need "):
                    continue  # lib.sh defines k()/kc(); `need` only lists required tools
                if "--context" in code:
                    continue  # explicitly pinned (for example in a printed hint)
                if re.search(r"(^|[\s;&|(])kubectl\s", code) and "command -v" not in code:
                    self.fail(f"{path.name}:{n} calls kubectl directly: {line.strip()}")

    def test_cluster_has_three_nodes_without_force_flag(self):
        deploy = read("deploy.sh")
        self.assertIn("--nodes 3", deploy)
        code = "\n".join(line.split("#", 1)[0] for line in deploy.splitlines())
        self.assertNotIn("--force", code)

    def test_nothing_pushes_to_a_remote(self):
        for path in ROOT.glob("*.sh"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("git push", text, path.name)
            self.assertNotIn("remote add", text, path.name)

    def test_scale_script_only_scales_stateless_apps(self):
        scale = read("scale.sh")
        self.assertIn("deployment/product-catalog", scale)
        self.assertIn("deployment/shopping-cart", scale)
        self.assertNotRegex(scale, r"scale\s+deployment/redis")

    def test_drain_script_always_uncordons(self):
        failover = read("failover.sh")
        self.assertIn("trap restore_node EXIT", failover)
        body = failover.split("restore_node() {")[1].split("}")[0]
        self.assertIn("uncordon", body)
        # The trap must be installed before the drain can run.
        self.assertLess(failover.index("trap restore_node EXIT"), failover.index("drain \"$node\""))


if __name__ == "__main__":
    unittest.main()
