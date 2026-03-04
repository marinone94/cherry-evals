// Maps task_type values to Tailwind color classes used across DatasetsPage and ExampleCard.
// Each entry: { bg, text } for badge styling.
export const TASK_TYPE_COLORS = {
  multiple_choice:       { bg: 'bg-blue-100',   text: 'text-blue-700'   },
  code_generation:       { bg: 'bg-purple-100', text: 'text-purple-700' },
  math_reasoning:        { bg: 'bg-amber-100',  text: 'text-amber-700'  },
  commonsense_reasoning: { bg: 'bg-green-100',  text: 'text-green-700'  },
  truthfulness:          { bg: 'bg-red-100',    text: 'text-red-700'    },
  science_qa:            { bg: 'bg-teal-100',   text: 'text-teal-700'   },
  reading_comprehension: { bg: 'bg-indigo-100', text: 'text-indigo-700' },
  physical_intuition:    { bg: 'bg-orange-100', text: 'text-orange-700' },
};

// Returns Tailwind classes for a task type, falling back to neutral gray.
export function taskTypeBadgeClasses(taskType) {
  const colors = TASK_TYPE_COLORS[taskType];
  if (colors) return `${colors.bg} ${colors.text}`;
  return 'bg-gray-100 text-gray-600';
}
