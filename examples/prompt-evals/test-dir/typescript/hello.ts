interface Person {
  name: string;
  age: number;
}
export const hello = (person: Person): string => {
  return `Hello ${person.name}, you are ${person.age} years old!`;
};
