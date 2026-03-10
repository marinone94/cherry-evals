export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Terms of Service</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: 10 March 2026</p>

      <div className="prose prose-sm text-gray-700 space-y-6">
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">1. Agreement</h2>
          <p>
            By accessing or using Cherry Evals (&quot;the Service&quot;), operated by Emilio Marinone
            (&quot;we&quot;, &quot;us&quot;), you agree to these Terms of Service (&quot;Terms&quot;).
            If you do not agree, do not use the Service. If you are using the Service on behalf of
            an organisation, you represent that you have authority to bind that organisation.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">2. Service Description</h2>
          <p>
            Cherry Evals is a platform for <strong>discovering, searching, curating, and exporting
            examples from public AI evaluation benchmark datasets</strong>. The Service is available
            via a web interface, REST API, CLI, and MCP server.
          </p>
          <p>
            Certain features (&quot;Intelligent Search&quot;, &quot;Agentic Ingestion&quot;,
            &quot;Custom Export&quot;) use large language models (LLMs) to assist with query
            interpretation, result ranking, dataset parsing, and format conversion. These features
            are clearly labelled and subject to per-tier usage quotas.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">3. Accounts and API Keys</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>You must provide a valid email address to create an account.</li>
            <li>You are responsible for all activity under your account and API keys.</li>
            <li>Do not share API keys. Treat them as passwords.</li>
            <li>Notify us immediately at <strong>security@cherryevals.com</strong> if you suspect unauthorised use.</li>
            <li>We may suspend or terminate accounts that violate these Terms.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">4. Acceptable Use</h2>
          <p>You may use the Service <strong>only</strong> for:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Searching and browsing public AI evaluation datasets.</li>
            <li>Creating, managing, and exporting curated collections of evaluation examples.</li>
            <li>Using LLM-powered features (intelligent search, agentic ingestion, custom export) for the above purposes.</li>
            <li>Integrating via the API, CLI, or MCP server for the above purposes.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">5. Prohibited Uses</h2>
          <p>You must <strong>not</strong>:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              <strong>Abuse LLM features</strong> &mdash; use intelligent search, agentic ingestion,
              or custom export to generate answers to evaluation questions, use the LLM as a
              general-purpose assistant, extract training data, or otherwise use LLM credits for
              purposes outside the product scope.
            </li>
            <li>
              <strong>Attempt prompt injection</strong> &mdash; craft search queries, format
              descriptions, or dataset descriptions designed to manipulate the behaviour of the
              underlying LLMs, bypass safety controls, or extract system prompts.
            </li>
            <li>
              <strong>Circumvent quotas or rate limits</strong> &mdash; create multiple accounts,
              rotate API keys, or use technical means to exceed your subscription tier limits.
            </li>
            <li>
              <strong>Scrape or bulk-download</strong> &mdash; systematically extract data beyond
              what is necessary for legitimate evaluation curation.
            </li>
            <li>
              <strong>Reverse-engineer</strong> &mdash; decompile, disassemble, or reverse-engineer
              any part of the Service (except as permitted by applicable law).
            </li>
            <li>
              <strong>Interfere with the Service</strong> &mdash; introduce malware, overload
              infrastructure, exploit vulnerabilities, or access other users&apos; data without
              authorisation.
            </li>
            <li>
              <strong>Ingest malicious content</strong> &mdash; submit datasets or descriptions
              containing prompt injection payloads, executable code, or content designed to
              compromise the Service or other users.
            </li>
            <li>
              <strong>Violate third-party rights</strong> &mdash; use the Service in a way that
              infringes intellectual property, privacy, or other rights of third parties.
            </li>
            <li>
              <strong>Use the Service for illegal purposes</strong> &mdash; violate any applicable
              law or regulation.
            </li>
          </ul>
          <p className="mt-2">
            Violation of these restrictions may result in immediate suspension or termination of
            your account without notice.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">6. Subscription Tiers and Billing</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              <strong>Free tier</strong>: keyword, semantic, and hybrid search; collection management;
              standard export formats. No LLM-powered features.
            </li>
            <li>
              <strong>Pro ($19/month)</strong> and <strong>Ultra ($49/month)</strong>: include
              intelligent search, agentic ingestion, and custom export, subject to daily quotas.
            </li>
            <li>New accounts receive a 7-day Ultra trial.</li>
            <li>Billing is handled by Polar.sh. By subscribing, you also agree to Polar.sh&apos;s terms of service.</li>
            <li>Subscriptions renew automatically. Cancel at any time; access continues until the end of the billing period.</li>
            <li>We reserve the right to change pricing with 30 days&apos; notice.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">7. Intellectual Property</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              <strong>Service</strong>: Cherry Evals is licensed under the Elastic License 2.0.
              You may use and modify the source code, but you may not provide the Service as a
              competing hosted offering.
            </li>
            <li>
              <strong>Datasets</strong>: evaluation datasets accessible through the Service are
              third-party works. You are responsible for complying with each dataset&apos;s licence
              (typically CC-BY, MIT, or Apache 2.0). We do not claim ownership of these datasets.
            </li>
            <li>
              <strong>Your collections</strong>: you retain ownership of the collections you create.
              By using the Service, you grant us a limited licence to process your collections for
              service delivery and to use anonymised, aggregated curation signals to improve the
              Service for all users.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">8. AI Transparency (EU AI Act)</h2>
          <p>
            In compliance with Article 50 of the EU AI Act, we disclose the following:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Features labelled &quot;Intelligent&quot;, &quot;Agentic&quot;, or &quot;AI-powered&quot; use large language models (Google Gemini, Anthropic Claude) to process your input.</li>
            <li>AI-generated results (search rankings, dataset parsers, export converters) are always presented for your review before being applied.</li>
            <li>No fully automated decisions with legal or significant effects are made by the Service.</li>
            <li>AI operations are logged for auditability. You may request access to logs related to your usage.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">9. Disclaimer of Warranties</h2>
          <p>
            The Service is provided &quot;as is&quot; and &quot;as available&quot;. To the maximum
            extent permitted by law, we disclaim all warranties, express or implied, including
            warranties of merchantability, fitness for a particular purpose, and non-infringement.
          </p>
          <p>
            We do not warrant that: (a) the Service will be uninterrupted or error-free;
            (b) AI-generated results will be accurate, complete, or suitable for your purpose;
            (c) evaluation datasets are free of errors or biases.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">10. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law, our total liability to you for all claims
            arising from or related to the Service shall not exceed the amount you paid us in the
            12 months preceding the claim. We are not liable for indirect, incidental, special,
            consequential, or punitive damages, including lost profits, data loss, or business
            interruption.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">11. Termination</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>You may delete your account at any time (see Privacy Policy for data deletion details).</li>
            <li>We may suspend or terminate your account for violation of these Terms, with or without notice depending on severity.</li>
            <li>Upon termination, your right to use the Service ceases immediately. We will delete your data in accordance with our Privacy Policy.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">12. Right of Withdrawal (EU Consumers)</h2>
          <p>
            If you are a consumer in the EU, you have a 14-day right of withdrawal from the date
            of purchase. However, by using the Service immediately after subscribing, you consent
            to the commencement of service delivery before the withdrawal period expires. Once you
            have used LLM-powered features, the right of withdrawal is waived to the extent of
            services already provided. To exercise the right of withdrawal, email{' '}
            <strong>legal@cherryevals.com</strong> within 14 days of purchase.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">13. Force Majeure</h2>
          <p>
            We are not liable for failure or delay in performing obligations due to events beyond
            our reasonable control, including but not limited to: natural disasters, pandemics,
            third-party service outages (Supabase, Polar.sh, Google, Anthropic), government actions,
            or internet infrastructure failures.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">14. Governing Law</h2>
          <p>
            These Terms are governed by the laws of Sweden. Disputes shall be resolved in the
            courts of Stockholm, Sweden. If you are a consumer in the EU, you retain the protection
            of mandatory provisions of the law of your country of residence, and you may bring
            proceedings in the courts of your country of residence.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">15. Severability</h2>
          <p>
            If any provision of these Terms is found to be invalid or unenforceable, the remaining
            provisions remain in full force and effect. The invalid provision shall be replaced by
            a valid provision that most closely achieves the intended economic purpose.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">16. Entire Agreement</h2>
          <p>
            These Terms, together with the Privacy Policy and Cookie Policy, constitute the entire
            agreement between you and Cherry Evals regarding the Service. They supersede all prior
            oral or written communications.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">17. Assignment</h2>
          <p>
            You may not assign your rights or obligations under these Terms without our prior
            written consent. We may assign our rights and obligations to a successor in connection
            with a merger, acquisition, or sale of all or substantially all of our assets.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">18. Changes</h2>
          <p>
            We may update these Terms. Material changes will be communicated via email or in-app
            notice at least 30 days before they take effect. Continued use after the effective
            date constitutes acceptance. If you disagree, you must stop using the Service and
            delete your account.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">19. Contact</h2>
          <p>
            Questions about these Terms: <strong>legal@cherryevals.com</strong>
          </p>
        </section>
      </div>
    </div>
  );
}
