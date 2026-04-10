'use client';

const features = [
  {
    title: 'Instant answers',
    description: 'Ask a question and get clear, conversational responses in seconds.',
  },
  {
    title: 'Write and edit faster',
    description: 'Draft emails, blog posts, social captions, and polished docs with ease.',
  },
  {
    title: 'Brainstorm anything',
    description: 'Generate ideas for products, lessons, projects, and plans whenever you are stuck.',
  },
  {
    title: 'Learn by doing',
    description: 'Get guided explanations, examples, and step-by-step help for complex topics.',
  },
  {
    title: 'Coding support',
    description: 'Plan features, debug errors, and scaffold code for modern frameworks.',
  },
  {
    title: 'Works everywhere',
    description: 'Use ChatGPT on desktop or mobile to stay productive anywhere.',
  },
];

const steps = [
  'Describe your goal in plain language.',
  'Refine the response with follow-up prompts.',
  'Copy, share, or continue the conversation.',
];

const testimonials = [
  {
    quote: 'ChatGPT helps our team turn rough ideas into launch-ready copy in minutes.',
    author: 'Maya R., Marketing Lead',
  },
  {
    quote: 'I use it daily for planning lessons and creating activities my students love.',
    author: 'Chris T., Educator',
  },
  {
    quote: 'From debugging to architecture planning, it is now part of my dev workflow.',
    author: 'Alex P., Software Engineer',
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto flex max-w-6xl flex-col gap-10 px-6 pb-20 pt-16 md:pt-24">
        <div className="inline-flex w-fit items-center rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
          Meet ChatGPT
        </div>

        <div className="max-w-3xl space-y-6">
          <h1 className="text-4xl font-semibold leading-tight md:text-6xl">
            Your everyday AI assistant for work, learning, and creativity.
          </h1>
          <p className="text-lg text-slate-300 md:text-xl">
            ChatGPT helps you write, learn, brainstorm, and build faster with natural conversations. Ask anything and get
            useful responses instantly.
          </p>
          <div className="flex flex-wrap gap-4">
            <button className="rounded-xl bg-emerald-400 px-5 py-3 font-medium text-slate-950 transition hover:bg-emerald-300">
              Start chatting
            </button>
            <button className="rounded-xl border border-slate-700 px-5 py-3 font-medium transition hover:border-slate-500 hover:bg-slate-900">
              Watch demo
            </button>
          </div>
        </div>

        <div className="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/50 p-5 md:grid-cols-3">
          <div>
            <p className="text-3xl font-semibold">100M+</p>
            <p className="text-slate-400">Weekly users worldwide</p>
          </div>
          <div>
            <p className="text-3xl font-semibold">24/7</p>
            <p className="text-slate-400">Always-on AI support</p>
          </div>
          <div>
            <p className="text-3xl font-semibold">50+</p>
            <p className="text-slate-400">Use cases from writing to coding</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <h2 className="mb-6 text-2xl font-semibold md:text-3xl">Why people choose ChatGPT</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <article key={feature.title} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
              <h3 className="mb-2 text-lg font-medium">{feature.title}</h3>
              <p className="text-slate-300">{feature.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid gap-6 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 md:grid-cols-2 md:p-8">
          <div>
            <h2 className="mb-4 text-2xl font-semibold md:text-3xl">Get started in three simple steps</h2>
            <p className="text-slate-300">No setup, no technical skills required. Open ChatGPT and start a conversation.</p>
          </div>
          <ol className="space-y-4">
            {steps.map((step, index) => (
              <li key={step} className="flex items-start gap-3">
                <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-400 font-semibold text-slate-900">
                  {index + 1}
                </span>
                <span className="text-slate-200">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="mb-6 text-2xl font-semibold md:text-3xl">What users are saying</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {testimonials.map((testimonial) => (
            <blockquote key={testimonial.author} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
              <p className="mb-4 text-slate-200">“{testimonial.quote}”</p>
              <footer className="text-sm text-slate-400">{testimonial.author}</footer>
            </blockquote>
          ))}
        </div>
      </section>
    </main>
  );
}
