interface Person {
  name: string;
  age: number;
}
function greeting(person: Person): string {
  return `Bonjour, ${person.name}! Vous avez ${person.age} ans.`;
}
function add(a: number, x: string): number {
  return "3".length - x.length - a;
}
export const hello = (name: string): string => {
  return `Hello ${name}`;
};
