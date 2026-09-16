def test_comments_restore_the_researcher_defined_stimulus_texts():
    """Do not silently rewrite the fixed experimental comments into a new voice."""
    from experiment_materials import load_materials

    materials = load_materials()
    comments = {
        article_id: [comment["text"] for comment in article["comments"]]
        for article_id, article in materials.items()
    }

    assert sum(map(len, comments.values())) == 40
    assert comments["A02"][0] == "文章开头把大学阶段的长期懈怠，与毕业后的就业困难直接联系起来。"
    assert comments["A03"][0] == "文章首先交代，长和把全球43个港口出售给了美国贝莱德集团。"
    assert comments["A04"][3] == "文章把火器封存看作一种短期维持差距、却牺牲长期发展的选择。"
    assert comments["A07"][9] == "作者最后提醒读者，这只是解释王朝寿命的一种片面视角。"
