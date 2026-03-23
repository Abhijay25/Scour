from dataclasses import dataclass, field


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass
class RankedResult:
    url: str
    title: str
    relevance_reason: str


@dataclass
class ExtractedContent:
    url: str
    title: str
    text: str
    success: bool
    error: str = ""


@dataclass
class CompetitorAnalysis:
    url: str
    title: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class CompetitiveEdge:
    ideas_to_steal: list[str] = field(default_factory=list)
    pitfalls_to_avoid: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass
class FullReport:
    query: str
    analyses: list[CompetitorAnalysis] = field(default_factory=list)
    edge: CompetitiveEdge | None = None
    markdown: str = ""
    saved_path: str = ""


@dataclass
class PipelineError(Exception):
    stage: str
    message: str

    def __str__(self) -> str:
        return f"[{self.stage}] {self.message}"
