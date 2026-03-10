export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: 10 March 2026</p>

      <div className="prose prose-sm text-gray-700 space-y-6">
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">1. Controller</h2>
          <p>
            Cherry Evals (&quot;we&quot;, &quot;us&quot;, &quot;the Service&quot;) is operated by
            Emilio Marinone, a sole proprietor based in the European Union.
            For data-protection enquiries: <strong>privacy@cherryevals.com</strong>.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">2. What We Collect and Why</h2>
          <table className="w-full text-sm border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2 border-b">Data</th>
                <th className="text-left p-2 border-b">Purpose</th>
                <th className="text-left p-2 border-b">Legal Basis (GDPR)</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="p-2">Email address</td>
                <td className="p-2">Account identification, billing, service communications</td>
                <td className="p-2">Performance of contract (Art. 6(1)(b))</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Supabase user ID</td>
                <td className="p-2">Authenticate requests, link data to account</td>
                <td className="p-2">Performance of contract (Art. 6(1)(b))</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">API key hash &amp; prefix</td>
                <td className="p-2">Programmatic authentication (raw key never stored)</td>
                <td className="p-2">Performance of contract (Art. 6(1)(b))</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Daily usage counters</td>
                <td className="p-2">Quota enforcement per subscription tier</td>
                <td className="p-2">Performance of contract (Art. 6(1)(b))</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Search queries &amp; curation events (pick, remove, export)</td>
                <td className="p-2">Service functionality; aggregated to improve search relevance for all users (&quot;collective intelligence&quot;)</td>
                <td className="p-2">Legitimate interest (Art. 6(1)(f)) &mdash; you may object (see Section 7)</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">IP address (transient)</td>
                <td className="p-2">Rate limiting; not persisted to database</td>
                <td className="p-2">Legitimate interest (Art. 6(1)(f))</td>
              </tr>
              <tr>
                <td className="p-2">Subscription &amp; payment metadata (via Polar.sh)</td>
                <td className="p-2">Tier assignment, billing reconciliation</td>
                <td className="p-2">Performance of contract (Art. 6(1)(b))</td>
              </tr>
            </tbody>
          </table>
          <p className="mt-2">
            We do <strong>not</strong> collect passwords (handled entirely by Supabase),
            payment card details (handled entirely by Polar.sh/Stripe), or biometric data.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">3. AI-Powered Features</h2>
          <p>
            When you use &quot;Intelligent Search&quot;, &quot;Agentic Ingestion&quot;, or &quot;Custom Export&quot;,
            your search query or format description is sent to third-party large language model (LLM)
            providers (currently Google Gemini and Anthropic Claude) for processing. These providers
            act as sub-processors and process data under their applicable data processing agreements.
          </p>
          <p>
            The LLMs are used <strong>only</strong> to interpret your search intent, rank results,
            generate dataset parsers, or produce export format converters. No automated decisions
            are made that produce legal or similarly significant effects on you. You always review
            and approve AI-generated results before they are applied.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">4. Sub-processors</h2>
          <table className="w-full text-sm border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2 border-b">Provider</th>
                <th className="text-left p-2 border-b">Role</th>
                <th className="text-left p-2 border-b">Location</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="p-2">Supabase Inc.</td>
                <td className="p-2">Authentication (JWT, OAuth)</td>
                <td className="p-2">US (EU project region available)</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Polar.sh</td>
                <td className="p-2">Subscription billing, webhooks</td>
                <td className="p-2">EU/US</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Google (Gemini API)</td>
                <td className="p-2">Embeddings, search intelligence, ingestion, export</td>
                <td className="p-2">US</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Anthropic (Claude API)</td>
                <td className="p-2">Advanced reasoning tasks</td>
                <td className="p-2">US</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Qdrant</td>
                <td className="p-2">Vector database (semantic search)</td>
                <td className="p-2">Self-hosted or Qdrant Cloud (EU/US)</td>
              </tr>
              <tr>
                <td className="p-2">Langfuse</td>
                <td className="p-2">Observability traces (dataset content only, no user PII)</td>
                <td className="p-2">EU</td>
              </tr>
            </tbody>
          </table>
          <p className="mt-2">
            Transfers to US-based sub-processors rely on EU Standard Contractual Clauses (SCCs)
            or the EU-US Data Privacy Framework where applicable. We maintain Data Processing
            Agreements (DPAs) with each sub-processor.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">5. Data Retention</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Account data</strong>: retained while your account is active. Deleted within 30 days of account deletion request.</li>
            <li><strong>Curation events</strong>: retained for 24 months for collective intelligence purposes, then anonymised (user_id removed) or deleted.</li>
            <li><strong>API key metadata</strong>: deleted when you revoke the key or delete your account.</li>
            <li><strong>Usage counters</strong>: reset daily; historical counts are not retained.</li>
            <li><strong>IP addresses</strong>: held in memory only for rate limiting; never persisted to disk.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">6. Cookies &amp; Local Storage</h2>
          <p>
            We use browser <code>localStorage</code> to store your authentication session token
            (provided by Supabase). This is a strictly necessary functional mechanism and does not
            require consent under the ePrivacy Directive. We do not use advertising cookies,
            analytics trackers, or third-party tracking scripts. See our{' '}
            <a href="/cookies" className="text-red-600 underline">Cookie Policy</a> for details.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">7. Your Rights (GDPR)</h2>
          <p>You have the right to:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Access</strong> &mdash; request a copy of all personal data we hold about you.</li>
            <li><strong>Rectification</strong> &mdash; correct inaccurate data.</li>
            <li><strong>Erasure</strong> &mdash; request deletion of your account and all associated data (&quot;right to be forgotten&quot;).</li>
            <li><strong>Data portability</strong> &mdash; receive your data in a structured, machine-readable format (JSON).</li>
            <li><strong>Restriction</strong> &mdash; request that we limit processing of your data.</li>
            <li><strong>Object</strong> &mdash; object to processing based on legitimate interest (e.g., curation event collection for collective intelligence).</li>
            <li><strong>Withdraw consent</strong> &mdash; where processing is based on consent, withdraw at any time.</li>
          </ul>
          <p className="mt-2">
            To exercise any right, email <strong>privacy@cherryevals.com</strong>. We will respond
            within 30 days. You also have the right to lodge a complaint with your local data
            protection authority. For users in Sweden, this is{' '}
            <strong>Integritetsskyddsmyndigheten (IMY)</strong> &mdash;{' '}
            <a href="https://www.imy.se" className="text-red-600 underline" target="_blank" rel="noopener noreferrer">www.imy.se</a>.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">8. Mandatory Data Provision</h2>
          <p>
            Providing your email address is required to create an account. If you choose not to
            provide it, you may still use the Service without an account (keyword, semantic, and
            hybrid search only). LLM-powered features, collections, and exports require an account.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">9. Security</h2>
          <p>
            We protect your data with: HTTPS encryption in transit, bcrypt/SHA-256 hashing for
            credentials, role-based access controls, rate limiting, and daily quota enforcement.
            API keys are stored as SHA-256 hashes; the raw key is shown once at creation and never
            stored. Despite these measures, no system is 100 % secure. If you discover a
            vulnerability, please report it to <strong>security@cherryevals.com</strong>.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">10. Children</h2>
          <p>
            Cherry Evals is not directed at individuals under 16. We do not knowingly collect data
            from children. If you believe a child has provided us with personal data, contact us and
            we will delete it.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">11. Changes</h2>
          <p>
            We may update this policy. Material changes will be communicated via email or an in-app
            notice at least 14 days before they take effect. Continued use after the effective date
            constitutes acceptance of the updated policy.
          </p>
        </section>
      </div>
    </div>
  );
}
