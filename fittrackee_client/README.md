# Rint web client

Vue 3 and TypeScript frontend for the Rint server. Use the committed npm lockfile.

```sh
npm ci
cp .env.example .env.local
npm run dev
```

The example points to the local Rint backend at `http://localhost:5080`.
Adjust `VITE_APP_API_URL` in `.env.local` if the backend uses another address.
Without a development override, the upstream fallback is port 5000.
Production builds always use the same-origin `/api/` endpoint.

To display the corresponding fork source on About, set `VITE_RINT_SOURCE_URL`
to its public HTTP(S) URL before building. Values beginning with `VITE_` are
included in the client bundle: do not put credentials in them.

```sh
npm run lint-check
npm run test:unit -- --run
npm run build
```

The production output goes to `../fittrackee/dist`, which the backend serves.
Restart a non-reloading backend after a build so it serves the new asset names.
Generated output and `.env.local` stay out of Git. See the root [setup guide](../RINT.md)
and [release preparation](../RELEASING.md) for the complete application.
