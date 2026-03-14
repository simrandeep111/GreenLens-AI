/** Format a CO2e value to a fixed decimal string */
export function formatCO2(val: number, decimals = 1): string {
  return val.toFixed(decimals);
}

/** Format a CAD currency value */
export function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(val);
}

/** Format a percentage */
export function formatPct(val: number, decimals = 1): string {
  return val.toFixed(decimals) + '%';
}

/** Calculate ESG score grade label from numeric score */
export function scoreGrade(score: number): string {
  if (score >= 80) return 'Leading';
  if (score >= 65) return 'Advanced';
  if (score >= 50) return 'Developing';
  return 'Emerging';
}
