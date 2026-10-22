import copy from "@/content/copy.json";
import { CopyButton } from "@/components/CopyButton";
import { formatUsd, readContent } from "@/lib/content";

const DOT = { GREEN: "🟢", AMBER: "🟡", RED: "🔴" } as const;
const labels = copy.demoLabels as Record<string, string>;

export default function Home() {
  const c = readContent();
  return (
    <main>
      <h1>{copy.title}</h1>
      <p className="tagline">{copy.tagline}</p>
      <p>{copy.problem}</p>
      <div className="card">
        {copy.colors.map((color) => (
          <p key={color.verdict}>
            <span className={`verdict ${color.verdict}`}>
              {DOT[color.verdict as keyof typeof DOT]} {color.verdict}
            </span>{" "}
            {color.rule}
          </p>
        ))}
      </div>

      <h2>Set up in 3 steps</h2>
      <ol>
        {copy.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <div className="card">
        <div className="row">
          <strong>Project instructions</strong>
          <CopyButton text={c.instructions} label="Copy instructions" />
        </div>
        <pre>{c.instructions}</pre>
      </div>
      <div className="card">
        <div className="row">
          <strong>Rules file (one per client)</strong>
          <span className="row">
            <CopyButton text={c.rulesTemplate} label="Copy rules file" />
            <a className="download" href="/client-rules.template.md" download="client-rules.md">
              Download
            </a>
          </span>
        </div>
        <pre>{c.rulesTemplate}</pre>
      </div>

      <h2>Try it</h2>
      <p>
        Make a Project with the instructions above and this example rules file for a made-up client, Acme Robotics.
        Then send the three messages below in order. Every company and person here is made up.
      </p>
      <div className="card">
        <div className="row">
          <strong>Example rules file: Acme Robotics</strong>
          <CopyButton text={c.acmeRules} label="Copy example rules" />
        </div>
        <pre>{c.acmeRules}</pre>
      </div>
      {c.stageSteps.map(({ input, message }) => (
        <div className="card" key={input.id}>
          <div className="row">
            <strong>{labels[input.id] ?? input.id}</strong>
            <CopyButton text={message} label="Copy message" />
          </div>
          <p className="note">
            Should come back:{" "}
            <span className={`verdict ${input.expected}`}>
              {DOT[input.expected]} {input.expected}
            </span>
          </p>
          <pre>{message}</pre>
        </div>
      ))}

      <h2>What it costs</h2>
      <p>
        In claude.ai it runs on your Claude plan, so there is no per-call charge. It counts toward your plan&apos;s usage
        like any other message. To show the real cost, the same check was run through the API:
      </p>
      {c.summary ? (
        <>
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Right verdict</th>
                <th>Per check</th>
                <th>Per 1,000 checks</th>
                <th>Avg time</th>
              </tr>
            </thead>
            <tbody>
              {c.summary.models.map((m) => (
                <tr key={m.model}>
                  <td>{m.label}</td>
                  <td>
                    {m.correct}/{m.checks}
                  </td>
                  <td>{formatUsd(m.avg_cost_usd)}</td>
                  <td>{formatUsd(m.avg_cost_usd * 1000)}</td>
                  <td>{m.avg_latency_s}s</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note">
            Measured {c.summary.generated}, {c.summary.runs} runs per input. Prices from{" "}
            <a href={c.summary.prices_source}>{c.summary.prices_source}</a>, checked {c.summary.prices_checked}.
          </p>
        </>
      ) : (
        <p className="note">Measurements are not published yet.</p>
      )}

      <h2>Limits</h2>
      <ul>
        {copy.limits.map((limit) => (
          <li key={limit}>{limit}</li>
        ))}
      </ul>

      <footer>
        Made by {copy.author.name} · <a href={`https://${copy.author.linkedin}`}>LinkedIn</a> ·{" "}
        <a href={`https://${copy.author.site}`}>{copy.author.site}</a> · Source:{" "}
        <a href={`https://${copy.repo}`}>{copy.repo}</a>
      </footer>
    </main>
  );
}
