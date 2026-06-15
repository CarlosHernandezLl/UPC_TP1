// app/page.tsx
import { redirect } from 'next/navigation';

export default function RootPage() {
  // Redirección nativa en el servidor hacia la carpeta (auth)/login
  redirect('/login');
}