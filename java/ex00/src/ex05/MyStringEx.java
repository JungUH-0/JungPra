package ex05;



class MyString {
	
	String str;
	char[] s = new char[50];
	
	public MyString(String str) {
		this.str = str;
		for(int i = 0; i <= str.length()-1; i++) 
			s[i] = str.charAt(i);
	}
	
	public String toString() {
		return str;
	}
	
	// 직접 구현
	public String concat(MyString str) {		
//		return this.str+str;
		String concatStr = new String();
		this.str +=str;
		concatStr = this.str;
		return concatStr;

	}
	
	public int compareTo(String other_str) {
		String str = this.str;
		int len1= str.length();
		int len2= other_str.length();
		int min  = Math.min(len1, len2);
		for (int i =0; i<min; i++) {
			char a1= str.charAt(i);
			char a2 = other_str.charAt(i);
			if (a1 != a2)
				return a1-a2;
		}
		return len1-len2; 
	}
	public boolean cotanins(CharSequence s) {
		String str = this.str ;
		 for (int i = 0; i <= str.length() - s.length(); i++) {
		        boolean match = true;
		        for (int j = 0; j < s.length(); j++) {
		            if (str.charAt(i + j) != s.charAt(j)) {
		                match = false;
		                break;
		            }
		        }
		        if (match) return true; 
		    }
		return false;
	}
	public String trim() {
		String str = this.str;
		String trimStr = new String();
		for(int i =0; i<str.length(); i++) {
			if(str.charAt(i)== ' ')
				continue;
			trimStr+= str.charAt(i);
		}
		return trimStr;
	}
	public String replace(String chk, String rpl) {
		int x = 0, y = 0;
		String outStr = new String();
		out:for(int i = 0; i < str.length(); i++) {
			String replace = new String();
			for(int j = i; j < str.length(); j++) {
				replace += str.charAt(j);
				System.out.println(replace);
				if(chk.equals(replace)) {
					x = j;	y = i;	break out;
				}
			}
		}
		System.out.println("확인:" + x + "," + y);
		for(int i = 0; i < y; i++)
			outStr += str.charAt(i);
		outStr += rpl;
		for(int j = x + 1; j < str.length(); j++)
			outStr += str.charAt(j);
		str = outStr;
		return outStr;
	}
	public String[] split(String s) {
		int count = 1;
	    for (int i = 0; i < s.length(); i++) {
	        if (s.charAt(i) == ' ') {
	            count++;
	        }
	    }

	    String[] result = new String[count];

	    int index = 0;
	    String temp = "";
	    for (int i = 0; i < s.length(); i++) {
	        if (s.charAt(i) == ' ') {
	            result[index] = temp;
	            temp = "";
	            index++;
	        } else {
	            temp += s.charAt(i);
	        }
	    }
	    result[index] = temp; // 마지막 토큰

	    return result;
	}
	public String substring(int index) {
		String str = this.str;
		char str_array [] = new char [str.length()] ;
		
		for (int i =index; i<str.length(); i++) {
			str_array[i]  = str.charAt(i);
		}
		String str1 = "";
		for(int i =index; i<str_array.length; i++) {
			str1 += str_array[i];
		}
		
		return str1;
	}
	public String toLowerCase(String s) {
		
		char s_arr [] = new char [s.length()];
		for (int i = 0; i<s.length(); i++) {
			s_arr[i] = s.charAt(i);
		}
		for (int i = 0; i<s.length(); i++) {
			if(65<=s_arr[i] && 90>=s_arr[i]) {
				s_arr[i] = (char)(s_arr[i]+32);
			}
		}
		String re = "";
		for (int i = 0; i<s_arr.length; i++) {
			re += s_arr[i];
		}
		return re;
	}
	public String toUpperCase(String s) {
		char s_arr [] = new char [s.length()];
		for (int i = 0; i<s.length(); i++) {
			s_arr[i] = s.charAt(i);
		}
		for (int i = 0; i<s.length(); i++) {
			if(97<=s_arr[i] && 122>=s_arr[i]) {
				s_arr[i] = (char)(s_arr[i]-32);
			}
		}
		String re = "";
		for (int i = 0; i<s_arr.length; i++) {
			re += s_arr[i];
		}
		return re;
		
	}
}


public class MyStringEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		MyString mystr= new MyString(" Hello we ");
		MyString newStr = new MyString("New World");
		System.out.println(mystr.toString());
//		for (int i = 0; i<mystr.toString().length(); i++) {
//			System.out.println(i);
//		}
//		System.out.println(mystr.s.length + "s는 이런거다");
		System.out.println(mystr.cotanins("we"));
		System.out.println(mystr.concat(newStr));
		System.out.println(mystr.substring(3));
		System.out.println(mystr.compareTo("New"));
		System.out.println(mystr.trim());
//		String s = "We are one";
//		char s_list [] = new char [s.length()];
//		for (int i = 0; i<s.length(); i++) {
//			s_list[i] = s.charAt(i);
// 		}
//		System.out.println(s_list[1]);
//		String a = "";
//		for (int i =3; i<s_list.length; i++) {
//			a +=s_list[i];
//		}
//		System.out.println(a);
		String s = new String(" we are world ");
		s= s.trim();
		System.out.println(s);
	}

}
