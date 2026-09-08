import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
from brew2fink.catalog import load
from brew2fink.core import plan, install
from brew2fink.cli import main

class TestBrew2Fink(unittest.TestCase):
    def test_catalog_and_near_hit_are_review_only(self):
        data={"relations":[{"source":{"manager":"homebrew","package_type":"formula","native_name":"ansible@12"},"target":{"manager":"fink","package_type":"package","native_name":"ansible"},"confidence":0.78,"matching_method":"version-family","review_status":"needs-review"}]}
        with tempfile.NamedTemporaryFile(mode="w") as stream:
            json.dump(data,stream); stream.flush()
            rows=plan([{"kind":"formula","name":"ansible@12"}],load(stream.name))
        self.assertEqual(install(rows)[0]["status"],"needs-review")
        self.assertEqual(rows[0]["catalog_version"], None)
        self.assertEqual(rows[0]["candidates"][0]["evidence"], [])

    def test_automatic_plan_preserves_core_metadata_and_dry_runs(self):
        data={"catalog_version":"catalog-test","relations":[{"source":{"manager":"homebrew","package_type":"formula","native_name":"wget"},"target":{"manager":"fink","package_type":"package","native_name":"wget"},"type":"equivalent","confidence":0.99,"matching_method":"upstream-identity","evidence":[{"kind":"homepage","value":"https://wget.example"}],"review_status":"automatic","source_catalog_versions":{"homebrew":"test"}}]}
        with tempfile.NamedTemporaryFile(mode="w") as stream:
            json.dump(data,stream); stream.flush()
            rows=plan([{"kind":"formula","name":"wget"}],load(stream.name))
        self.assertEqual(rows[0]["catalog_version"], "catalog-test")
        recommendation=rows[0]["recommendation"]
        self.assertEqual(recommendation["target"]["native_name"], "wget")
        self.assertEqual(recommendation["review_status"], "automatic")
        self.assertEqual(recommendation["evidence"][0]["kind"], "homepage")
        result=install(rows, apply=False)
        self.assertEqual(result[0]["status"], "dry-run")
        self.assertEqual(result[0]["command"], ["fink", "install", "wget"])

    def test_apply_checks_fink_target_before_installing(self):
        data={"catalog_version":"catalog-test","relations":[{"source":{"manager":"homebrew","package_type":"formula","native_name":"wget"},"target":{"manager":"fink","package_type":"package","native_name":"wget"},"confidence":0.99,"matching_method":"curated","evidence":[{"kind":"curated"}],"review_status":"automatic"}]}
        with tempfile.NamedTemporaryFile(mode="w") as stream:
            json.dump(data,stream); stream.flush()
            rows=plan([{"kind":"formula","name":"wget"}],load(stream.name))
        calls=[]
        class Result:
            returncode=1
            stdout=""
        def run(command, **kwargs):
            calls.append(command)
            return Result()
        result=install(rows, apply=True, run=run)
        self.assertEqual(result[0]["status"], "target-missing")
        self.assertEqual(calls, [["fink", "list", "wget"]])

    def test_no_argument_guide_has_review_dry_run_apply_verify_sequence(self):
        output=StringIO()
        with patch("sys.argv", ["brew2fink"]), redirect_stdout(output):
            main()
        guide=output.getvalue()
        for text in (
            "brew2fink prepare",
            "Review migration-preview.csv",
            "brew2fink migrate --plan migration-plan.json",
            "brew2fink migrate --plan migration-plan.json --install",
            "brew2fink verify --plan migration-plan.json",
            "never removed automatically",
        ):
            self.assertIn(text, guide)
