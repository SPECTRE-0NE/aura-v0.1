import * as React from 'react';

export const Card: React.FC<React.PropsWithChildren<{title?: string}>> = ({ title, children }) => (
  <div className="rounded-2xl border p-4 shadow-sm">
    {title && <div className="mb-2 text-sm font-semibold opacity-80">{title}</div>}
    <div>{children}</div>
  </div>
);

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ children, ...props }) => (
  <button className="rounded-xl border px-4 py-2 transition hover:shadow" {...props}>{children}</button>
);
