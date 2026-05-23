import { analysisReportSchema, analyzeLinkRequestSchema, type AnalysisReport, type AnalyzeLinkRequest } from "@scout/shared";

export interface AiClient {
  analyze(payload: AnalyzeLinkRequest): Promise<AnalysisReport>;
}

export function createAiClient(baseUrl: string): AiClient {
  return {
    async analyze(payload) {
      const body = analyzeLinkRequestSchema.parse(payload);
      const response = await fetch(`${baseUrl}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`AI service failed with status ${response.status}`);
      }

      const result = await response.json();
      return analysisReportSchema.parse(result);
    },
  };
}
