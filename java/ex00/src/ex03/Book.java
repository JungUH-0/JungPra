package ex03;

public class Book {
	String title;
	String author;
	
	public Book(String t ) {//생성자
		title=t; author="작자미상";
		
	}
	public Book(String t , String a ) {
		title=t;author=a;
	}

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Book littlePrince = new Book("어린왕자","생텍쥐페리");
		Book loveStroy = new Book("춘향전");
		System.out.println(littlePrince.title + " "+ littlePrince.author );
		System.out.println(loveStroy.title+ " "+ loveStroy.author);

	}

}
