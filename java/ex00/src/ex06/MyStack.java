package ex06;
class GStack<T>{
	int tos;
	Object[] stck;
	public GStack() {
		tos=0;
		stck = new Object[10];
	}
	public void push(T item) {
		if(tos == 10)
			return;
		stck[tos]= item;
		tos++;
	}
	public T pop() {
		if(tos == 0)
			return null;
		tos --;
		return (T)stck[tos];
	}
}
public class MyStack {
	public static <T> GStack<T> reverse(GStack<T> a){
		GStack<T> s = new GStack<T>();
		while(true) {
			T tmp;
			tmp = a.pop();//원래 스택에서 요소하나 꺼냄
			if(tmp==null)// 스택이 비었음
				break;
			else 
				s.push(tmp);//새 스택에 요소 삽입
		}
		return s;
	}
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		GStack<String> stringStack = new GStack<String>();
		stringStack.push("seoul");
		stringStack.push("busan");
		stringStack.push("LA");
		
		for(int n=0; n<3; n++) 
			System.out.println(stringStack.pop());
			
		GStack<Integer>intStack = new GStack<Integer>();
		
		intStack.push(1);
		intStack.push(3);
		intStack.push(5);
		
		for(int n=0; n<3; n++) 
			System.out.println(intStack.pop());
		
		GStack<Double> gs = 
				new GStack<Double>();
		for(int i = 0; i <5; i++) {
			gs.push(new Double(i));
		}
		gs=reverse(gs);
		for(int i = 0; i <5; i++) {
			System.out.println(gs.pop());
		}
		

	}

}
