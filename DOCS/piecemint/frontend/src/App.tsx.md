# Root React component: router and data provider

**Source file:** `piecemint/frontend/src/App.tsx`

## Overview

- Wraps the app in **`BrowserRouter`**, **`FinanceDataProvider`**, and **`Routes`** with **`AppLayout`** as the parent route.

- Routes: **`/`** Overview, **`/analytics`**, **`/contacts`**, **`/activity`**, **`/budget`**, **`/financial-settings`**, **`/prices`**, **`/library`**, redirects **`/marketplace`** → **`/library`**, **`/docs/plugins`**, **`/plugin/:pluginId`**.
