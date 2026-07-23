from pathlib import Path

from pictovap.core.primitives import CMSPlacement, PlacementInstruction
from pictovap.testing import assert_cms_adapter_contract
from pictovap_hugo import HugoAdapter


def _placement(article_id: str = "posts/sample.md") -> CMSPlacement:
    return CMSPlacement(
        article_id=article_id,
        placements=[
            PlacementInstruction(
                slot_id="section_0",
                output_path="/tmp/pictovap/market.webp",
                target_section="Where to eat",
                alt_text="Market stall",
                caption="Local market",
            )
        ],
    )


def test_adapter_contract_without_content_dir():
    result = assert_cms_adapter_contract(HugoAdapter())
    assert result["warnings"] == ["content_dir is not configured; no Hugo files were written"]


def test_adapter_inserts_shortcode_after_target_heading(tmp_path):
    content_dir = tmp_path / "content"
    article = content_dir / "posts/sample.md"
    article.parent.mkdir(parents=True)
    article.write_text("# Guide\n\n## Where to eat\n\nOriginal paragraph.\n", encoding="utf-8")

    result = assert_cms_adapter_contract(
        HugoAdapter(str(content_dir)),
        placement=_placement(),
    )

    text = article.read_text(encoding="utf-8")
    assert result["placed"][0]["slot_id"] == "section_0"
    assert '<!-- pictovap:section_0:start -->' in text
    assert '{{< figure src="/images/pictovap/market.webp" alt="Market stall" caption="Local market" >}}' in text
    assert text.index("## Where to eat") < text.index("pictovap:section_0:start")


def test_adapter_replaces_existing_marker_without_duplicate(tmp_path):
    content_dir = tmp_path / "content"
    article = content_dir / "posts/sample.md"
    article.parent.mkdir(parents=True)
    article.write_text("# Guide\n\n## Where to eat\n\nOriginal paragraph.\n", encoding="utf-8")

    adapter = HugoAdapter(str(content_dir))
    adapter.place(_placement())
    adapter.place(_placement())

    text = article.read_text(encoding="utf-8")
    assert text.count("pictovap:section_0:start") == 1
    assert text.count("{{< figure") == 1


def test_adapter_rejects_article_paths_outside_content_dir(tmp_path):
    result = HugoAdapter(str(tmp_path / "content")).place(_placement("../escape.md"))

    assert result["placed"] == []
    assert result["failed"][0]["error"] == "article_id must resolve inside content_dir"
    assert not Path(tmp_path / "escape.md").exists()
