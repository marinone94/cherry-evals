export default function CookiePage() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Cookie Policy</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: 10 March 2026</p>

      <div className="prose prose-sm text-gray-700 space-y-6">
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">1. Overview</h2>
          <p>
            Cherry Evals uses minimal browser storage, limited to what is strictly necessary for
            the Service to function. We do <strong>not</strong> use advertising cookies, analytics
            trackers, social media pixels, or any third-party tracking scripts.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">2. What We Store</h2>
          <table className="w-full text-sm border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2 border-b">Name / Key</th>
                <th className="text-left p-2 border-b">Type</th>
                <th className="text-left p-2 border-b">Purpose</th>
                <th className="text-left p-2 border-b">Duration</th>
                <th className="text-left p-2 border-b">Category</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="p-2"><code>sb-*-auth-token</code></td>
                <td className="p-2">localStorage</td>
                <td className="p-2">
                  Stores your Supabase authentication session (JWT access token and refresh token)
                  so you remain signed in across page loads.
                </td>
                <td className="p-2">Until sign-out or token expiry</td>
                <td className="p-2">Strictly necessary</td>
              </tr>
            </tbody>
          </table>
          <p className="mt-3">
            <strong>That&apos;s it.</strong> We have no other cookies, local storage entries,
            session storage entries, or IndexedDB databases.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">3. Third-Party Cookies</h2>
          <p>
            Cherry Evals does not load any third-party scripts that set cookies. We do not use
            Google Analytics, Meta Pixel, Hotjar, Intercom, or any other analytics or marketing
            tool. The landing page at cherryevals.com is fully static with no external
            dependencies.
          </p>
          <p>
            When you sign in via a third-party OAuth provider (e.g., Google, GitHub) through
            Supabase, the provider&apos;s own authentication flow may set cookies on their domain.
            These cookies are governed by the provider&apos;s privacy policy, not ours.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">4. Why No Cookie Banner?</h2>
          <p>
            Under the ePrivacy Directive (2002/58/EC, as amended by 2009/136/EC) and its national
            implementations, consent is not required for storage that is &quot;strictly
            necessary&quot; for a service explicitly requested by the user. Our sole use of
            <code>localStorage</code> &mdash; keeping you signed in &mdash; falls squarely within
            this exemption.
          </p>
          <p>
            If we ever add non-essential cookies or trackers in the future, we will implement a
            consent mechanism before doing so.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">5. How to Clear Stored Data</h2>
          <p>You can remove your authentication session at any time by:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Clicking &quot;Sign out&quot; in the app (this clears the localStorage entry).</li>
            <li>Manually clearing your browser&apos;s local storage for the app.cherryevals.com domain.</li>
            <li>Using your browser&apos;s &quot;Clear site data&quot; or &quot;Clear browsing data&quot; feature.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">6. Changes</h2>
          <p>
            If we change what we store in your browser, we will update this page. If we introduce
            non-essential cookies, we will ask for your consent before setting them.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mt-6 mb-2">7. Contact</h2>
          <p>
            Questions about cookies or browser storage: <strong>privacy@cherryevals.com</strong>
          </p>
        </section>
      </div>
    </div>
  );
}
