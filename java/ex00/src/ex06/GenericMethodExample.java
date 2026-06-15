package ex06;


public class GenericMethodExample {
	//T가 타입 매개변수인 제네릭 메소드
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
		//Double 타입의 GStack 생성
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
