
const API =
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000'


export async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {

  const response = await fetch(
    `${API}${path}`,
    options
  )

  if (!response.ok) {

    const detail = await response.text()

    throw new Error(
      detail || `Request failed: ${response.status}`
    )

  }

  return response.json() as Promise<T>

}


export type Finding = {

  id: number

  title: string

  category: string

  severity: string

  status: string

  explanation: string

  vendor_id: number | null

  invoice_id: number | null

}


export type Metrics = {

  vendors: number

  documents: number

  purchase_orders: number

  invoices: number

  open_findings: number

  high_risk: number

}
