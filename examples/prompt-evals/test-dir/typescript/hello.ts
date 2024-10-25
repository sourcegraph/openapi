interface Person {
  name: string;
  age: number;
}

interface Animal {
  name: string;
  species: string;
}

class Dog implements Animal {
  name= "dog"
  species = "mammal"
}

export const hello = (person: Person): string => {
  return `Hello ${person.name}, you are ${person.age} years old!`;
};
