"""AI-powered content generation tied to content plans."""

from __future__ import annotations

from sqlalchemy.orm import Session

from socialmonitor.db.models import ContentPlan, GeneratedContent, TrendItem
from socialmonitor.utils.llm import generate_text, get_model_name


SYSTEM_PROMPT = """\
You are an expert social-media content creator specialising in AI and technology.
You write engaging, informative posts that drive interaction.
Adapt your tone and length to the target platform.
"""


class ContentGenerator:
    """Generate content using LLMs, informed by trends and plan details."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def generate_for_plan(
        self, plan_id: int, extra_context: str = ""
    ) -> GeneratedContent:
        """Generate content for an existing plan."""
        plan = self.session.get(ContentPlan, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        prompt = self._build_prompt(plan, extra_context)
        body = await generate_text(prompt, system=SYSTEM_PROMPT, max_tokens=1500)

        # Determine next version number
        existing = (
            self.session.query(GeneratedContent)
            .filter(GeneratedContent.plan_id == plan_id)
            .count()
        )

        content = GeneratedContent(
            plan_id=plan_id,
            version=existing + 1,
            body=body,
            model_used=get_model_name(),
            prompt_used=prompt,
        )
        self.session.add(content)
        self.session.commit()
        return content

    async def generate_from_trends(
        self, platform: str = "twitter", content_type: str = "post"
    ) -> tuple[ContentPlan, GeneratedContent]:
        """Auto-create a plan from current trends and generate content for it."""
        # Grab recent AI trends
        trends = (
            self.session.query(TrendItem)
            .filter(TrendItem.category == "ai")
            .order_by(TrendItem.id.desc())
            .limit(10)
            .all()
        )

        trend_summary = "\n".join(
            f"- {t.title} (score: {t.score})" for t in trends
        ) or "No trend data available yet."

        # Create a plan
        plan = ContentPlan(
            title="AI Trend Post (auto-generated)",
            platform=platform,
            content_type=content_type,
            topic="Current AI trends",
            notes=f"Based on trends:\n{trend_summary}",
            status="draft",
        )
        self.session.add(plan)
        self.session.flush()

        prompt = self._build_prompt(plan, extra_context=f"Current trending topics:\n{trend_summary}")
        body = await generate_text(prompt, system=SYSTEM_PROMPT, max_tokens=1500)

        content = GeneratedContent(
            plan_id=plan.id,
            version=1,
            body=body,
            model_used=get_model_name(),
            prompt_used=prompt,
        )
        self.session.add(content)
        self.session.commit()
        return plan, content

    async def suggest_topics(self, count: int = 5) -> list[str]:
        """Use the LLM to suggest content topics based on stored trends."""
        trends = (
            self.session.query(TrendItem)
            .order_by(TrendItem.id.desc())
            .limit(20)
            .all()
        )
        trend_list = "\n".join(f"- {t.title}" for t in trends) or "No trends stored yet."

        prompt = (
            f"Based on these trending topics in AI and tech:\n{trend_list}\n\n"
            f"Suggest {count} compelling content ideas for a social media creator "
            f"who covers AI. For each, give a one-line title and a brief description. "
            f"Format: numbered list."
        )
        result = await generate_text(prompt, system=SYSTEM_PROMPT, max_tokens=800)
        return [line.strip() for line in result.strip().split("\n") if line.strip()]

    def get_generated_content(self, plan_id: int) -> list[GeneratedContent]:
        """Return all generated versions for a plan."""
        return (
            self.session.query(GeneratedContent)
            .filter(GeneratedContent.plan_id == plan_id)
            .order_by(GeneratedContent.version)
            .all()
        )

    def select_version(self, content_id: int) -> GeneratedContent | None:
        """Mark a generated version as the selected one."""
        content = self.session.get(GeneratedContent, content_id)
        if not content:
            return None
        # Deselect any previously selected version for the same plan
        self.session.query(GeneratedContent).filter(
            GeneratedContent.plan_id == content.plan_id
        ).update({"is_selected": False})
        content.is_selected = True
        self.session.commit()
        return content

    # ---- Helpers -------------------------------------------------------------

    @staticmethod
    def _build_prompt(plan: ContentPlan, extra_context: str = "") -> str:
        platform_guides = {
            "twitter": "Max 280 chars. Punchy, use hashtags sparingly. Conversational tone.",
            "linkedin": "Professional tone, 1-3 paragraphs. Can use bullet points.",
            "youtube": "Write a video script outline with hook, key points, and CTA.",
            "blog": "Long-form article, 500-1000 words. Include intro, body with subheadings, conclusion.",
            "instagram": "Caption style. Engaging opening line, value-driven body, CTA. Suggest hashtags at end.",
        }

        guide = platform_guides.get(plan.platform or "", "Write an engaging social media post.")

        parts = [
            f"Create a {plan.content_type or 'post'} for {plan.platform or 'social media'}.",
            f"Topic: {plan.topic or plan.title}",
            f"Platform guidelines: {guide}",
        ]
        if plan.notes:
            parts.append(f"Additional notes: {plan.notes}")
        if extra_context:
            parts.append(f"Context: {extra_context}")

        return "\n\n".join(parts)
