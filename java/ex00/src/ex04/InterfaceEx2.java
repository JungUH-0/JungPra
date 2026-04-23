package ex04;
//interface PhoneInterface{
//	final int TIMEOUT = 10000; //상수 필드 선언
//	void sendCall();
//	void receiveCall();
//	default void printLogo() {
//		System.out.println("**Phone**");
//	}
//}
interface MobilePhoneInterface extends PhoneInterface{
	void sendSMS();
	void receiveSMS();
}
interface MP3Interface{
	public void play();
	public void stop();
}
class PDA{
	public int calculate(int x, int y) {
		return x+y;
	}
}
//SmartPhone 클래스는 PDA를 상속 받고,
//MobilePhoneInterface 와 MP3Interface 인터페이스에 선언된 추상 메소드를 모두 구현한다.
class SmartPhone extends PDA implements MobilePhoneInterface, MP3Interface{
	//MobilePhoneInterface 의 추상 메소드 구현
	@Override
	public void sendCall() {
		// TODO Auto-generated method stub
		System.out.println("따르릉따르릉~~");
	}

	@Override
	public void receiveCall() {
		// TODO Auto-generated method stub
		System.out.println("전화가 왔어요.");
	}

	@Override
	public void play() {
		// TODO Auto-generated method stub
		System.out.println("음악을 연주합니다.");
	}

	@Override
	public void stop() {
		// TODO Auto-generated method stub
		System.out.println("음악을 중단합니다.");
	}

	@Override
	public void sendSMS() {
		// TODO Auto-generated method stub
		System.out.println("문자갑니다.");
	}

	@Override
	public void receiveSMS() {
		// TODO Auto-generated method stub
		System.out.println("문자왔어요.");
	}
	//추가 작성 메소드
	public void schedule() {
		System.out.println("일정 관리합니다."); }
	
}
public class InterfaceEx2 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub

		SmartPhone phone = new SmartPhone();
		phone.printLogo();
		phone.sendCall();
		phone.play();
		System.out.println("3과 5를 더하면 " + phone.calculate(3,5));
		phone.schedule();
	}

}
