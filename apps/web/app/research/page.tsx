import { Label, Panel } from "@/components/ui/panel";

export default function ResearchPage() {
  return (
    <div className="space-y-4">
      <Label>Research mode</Label>
      <h1 className="font-serif text-4xl">No foundation model is bundled</h1>
      <Panel>
        <p>The default provider is deterministic: it plans with rules and narrates from tool output. An OpenAI-compatible endpoint can be configured with AEON_LLM_BASE_URL and AEON_LLM_API_KEY. If its narration contains numbers that are not in the evidence, the narration is dropped.</p>
        <p className="mt-3 text-mute">LoRA, PEFT, and literature retrieval are extension points. The reference table stays empty rather than holding invented citations.</p>
      </Panel>
    </div>
  );
}
