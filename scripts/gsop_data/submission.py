"""E7: render the submission text from a template. Every number comes from claims.csv; the E32 sentence from docs/E32.txt."""
import json
import os
import re

from .claims import NUM_RE, read_claims, text_numbers

PLACEHOLDER = re.compile(r"\{\{(claim:[^}\s]+|e32|india_region|india_tiles)\}\}")


class SubmissionError(Exception):
    pass


def render(root):
    with open(os.path.join(root, "submission/template.md"), encoding="utf-8") as f:
        template = f.read()
    claims = {c[0]: c[1] for c in read_claims(os.path.join(root, "public/data/claims.csv"))}
    with open(os.path.join(root, "docs/E32.txt"), encoding="utf-8") as f:
        e32 = f.read().rstrip("\n")

    with open(os.path.join(root, "public/data/regions.json"), encoding="utf-8") as f:
        regions = json.load(f)["regions"]
    india = [r for r in regions if r["n_tiles_in_india"] > 0]

    def sub(m):
        key = m.group(1)
        if key == "e32":
            return e32
        if key in ("india_region", "india_tiles"):
            # The India paragraph says exactly one listed region overlaps the outline. If that stops being true, stop.
            if len(india) != 1:
                raise SubmissionError(f"the India paragraph assumes one region overlaps India, but {len(india)} do; rewrite it")
            rid = india[0]["id"]
            if key == "india_region":
                return rid
            cid = f"regions.{rid.replace(' ', '_')}.n_tiles_in_india"
            if cid not in claims:
                raise SubmissionError(f"no claims.csv row for {cid}")
            return claims[cid]
        cid = key[len("claim:") :]
        if cid not in claims:
            raise SubmissionError(f"no claims.csv row for {cid}")
        return claims[cid]

    return PLACEHOLDER.sub(sub, template)


def typed_numbers(template):
    """Numbers typed into the template outside placeholders. There must be none."""
    stripped = PLACEHOLDER.sub("", template)
    stripped = re.sub(r"https?://\S+", "", stripped)  # addresses are not statistics
    return text_numbers(stripped)
