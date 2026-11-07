from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    title: str
    content: str
    table_data: list[list[str]] | None = None


class GenerateReportRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Report headline or title")
    subtitle: str | None = Field(default=None, description="Report subtitle or scope")
    author_name: str | None = Field(default="BioInsight AI Researcher", description="Author or investigator")
    summary: str = Field(..., description="Executive scientific summary")
    sections: list[ReportSection] = Field(default=[], description="Structured scientific report sections")
    references: list[str] = Field(default=[], description="Citations and database links")
