package ex04;
interface PhoneInterface{
	final int TIMEOUT = 10000; //상수 필드 선언
	void sendCall();
	void receiveCall();
	default void printLogo() {
		System.out.println("**Phone**");
	}
}
class SamsungPhone implements PhoneInterface{
	public void sendCall() {
		System.out.println("띠리리리링");
	}
	public void receiveCall() {
		System.out.println("전화가 왔습니다.");
	}
	public void flash() {
		System.out.println("전화기에 불이 켜졌습니다.");
	}
}
public class InterfaceEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		SamsungPhone phone = new SamsungPhone();
		phone.printLogo();
		phone.sendCall();
		phone.receiveCall();
		phone.flash();

	}

}
